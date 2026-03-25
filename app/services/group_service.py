from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session, joinedload

from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit
from app.models.group import Group
from app.models.group_member import GroupMember
from app.models.settlement_payment import SettlementPayment
from app.models.user import User


TWOPLACES = Decimal("0.01")


class GroupService:
    def __init__(self, db: Session):
        self.db = db

    def create_group(self, name: str, members: list[str], current_user: User) -> Group:
        group = Group(name=name, created_by=current_user.id)
        self.db.add(group)
        self.db.flush()

        member_ids = {current_user.id}
        for mobile in members:
            user = self.db.query(User).filter(User.mobile == mobile).first()
            if not user:
                raise ValueError(f"User with mobile {mobile} does not exist")
            member_ids.add(user.id)

        for user_id in member_ids:
            self.db.add(GroupMember(group_id=group.id, user_id=user_id))

        self.db.commit()
        return self.get_group(group.id, current_user)

    def list_groups(self, current_user: User) -> list[Group]:
        return (
            self.db.query(Group)
            .join(GroupMember, GroupMember.group_id == Group.id)
            .options(
                joinedload(Group.members).joinedload(GroupMember.user),
                joinedload(Group.expenses).joinedload(Expense.splits).joinedload(ExpenseSplit.user),
                joinedload(Group.expenses).joinedload(Expense.payer),
                joinedload(Group.settlements).joinedload(SettlementPayment.from_user),
                joinedload(Group.settlements).joinedload(SettlementPayment.to_user),
            )
            .filter(GroupMember.user_id == current_user.id)
            .order_by(Group.id.desc())
            .all()
        )

    def get_group(self, group_id: int, current_user: User) -> Group:
        group = (
            self.db.query(Group)
            .join(GroupMember, GroupMember.group_id == Group.id)
            .options(
                joinedload(Group.members).joinedload(GroupMember.user),
                joinedload(Group.expenses).joinedload(Expense.splits).joinedload(ExpenseSplit.user),
                joinedload(Group.expenses).joinedload(Expense.payer),
                joinedload(Group.settlements).joinedload(SettlementPayment.from_user),
                joinedload(Group.settlements).joinedload(SettlementPayment.to_user),
            )
            .filter(Group.id == group_id, GroupMember.user_id == current_user.id)
            .first()
        )
        if not group:
            raise ValueError("Group not found")
        return group

    def add_expense(
        self,
        group_id: int,
        title: str,
        amount: Decimal,
        paid_by: int,
        split_type: str,
        split_between: list[int],
        custom_splits: list[dict],
        current_user: User,
    ) -> Group:
        group = self.get_group(group_id, current_user)
        member_ids = {member.user_id for member in group.members}
        if paid_by not in member_ids:
            raise ValueError("Payer must be a group member")
        if not split_between:
            raise ValueError("At least one split member is required")
        if any(user_id not in member_ids for user_id in split_between):
            raise ValueError("Every split member must belong to the group")

        expense = Expense(
            group_id=group_id,
            title=title,
            amount=self._q(amount),
            paid_by=paid_by,
            split_type=split_type,
        )
        self.db.add(expense)
        self.db.flush()

        splits = self._build_splits(expense.id, amount, split_type, split_between, custom_splits)
        for split in splits:
            self.db.add(split)

        self.db.commit()
        return self.get_group(group_id, current_user)

    def get_balances(self, group_id: int, current_user: User) -> dict:
        group = self.get_group(group_id, current_user)
        members = {member.user_id: member.user for member in group.members}
        net_map: dict[int, Decimal] = {user_id: Decimal("0.00") for user_id in members}

        for expense in group.expenses:
            net_map[expense.paid_by] += self._q(expense.amount)
            for split in expense.splits:
                net_map[split.user_id] -= self._q(split.share_amount)

        for payment in group.settlements:
            net_map[payment.from_user_id] += self._q(payment.amount)
            net_map[payment.to_user_id] -= self._q(payment.amount)

        balances = []
        for user_id, net in net_map.items():
            quantized = self._q(net)
            status = "settled"
            if quantized > 0:
                status = "get"
            elif quantized < 0:
                status = "owe"
            balances.append(
                {
                    "user_id": user_id,
                    "name": members[user_id].name,
                    "net_balance": quantized,
                    "status": status,
                }
            )

        return {
            "group_id": group.id,
            "balances": balances,
            "settlements": self._simplify_balances(net_map, members),
        }

    def settle_payment(
        self,
        group_id: int,
        from_user_id: int,
        to_user_id: int,
        amount: Decimal,
        current_user: User,
    ) -> Group:
        group = self.get_group(group_id, current_user)
        member_ids = {member.user_id for member in group.members}
        if from_user_id not in member_ids or to_user_id not in member_ids:
            raise ValueError("Settlement users must belong to the group")
        if from_user_id == to_user_id:
            raise ValueError("Settlement payer and receiver must be different")

        self.db.add(
            SettlementPayment(
                group_id=group.id,
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                amount=self._q(amount),
            )
        )
        self.db.commit()
        return self.get_group(group.id, current_user)

    def _build_splits(
        self,
        expense_id: int,
        amount: Decimal,
        split_type: str,
        split_between: list[int],
        custom_splits: list[dict],
    ) -> list[ExpenseSplit]:
        total = self._q(amount)
        if split_type == "equal":
            return self._equal_splits(expense_id, total, split_between)
        if split_type == "custom":
            return self._custom_splits(expense_id, total, split_between, custom_splits)
        raise ValueError("Unsupported split type")

    def _equal_splits(self, expense_id: int, amount: Decimal, split_between: list[int]) -> list[ExpenseSplit]:
        base = (amount / len(split_between)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        splits: list[ExpenseSplit] = []
        running_total = Decimal("0.00")
        for index, user_id in enumerate(split_between):
            share = base
            if index == len(split_between) - 1:
                share = self._q(amount - running_total)
            running_total += share
            splits.append(ExpenseSplit(expense_id=expense_id, user_id=user_id, share_amount=share))
        return splits

    def _custom_splits(
        self,
        expense_id: int,
        amount: Decimal,
        split_between: list[int],
        custom_splits: list[dict],
    ) -> list[ExpenseSplit]:
        split_map = {entry["user_id"]: self._q(entry["share_amount"]) for entry in custom_splits}
        if set(split_map.keys()) != set(split_between):
            raise ValueError("Custom split members must match split_between users")
        total = sum(split_map.values(), Decimal("0.00"))
        if self._q(total) != self._q(amount):
            raise ValueError("Custom split total must equal expense amount")
        return [
            ExpenseSplit(expense_id=expense_id, user_id=user_id, share_amount=split_map[user_id])
            for user_id in split_between
        ]

    def _simplify_balances(self, net_map: dict[int, Decimal], members: dict[int, User]) -> list[dict]:
        creditors = []
        debtors = []

        for user_id, net in net_map.items():
            balance = self._q(net)
            if balance > 0:
                creditors.append({"user_id": user_id, "amount": balance})
            elif balance < 0:
                debtors.append({"user_id": user_id, "amount": abs(balance)})

        creditors.sort(key=lambda item: item["amount"], reverse=True)
        debtors.sort(key=lambda item: item["amount"], reverse=True)

        entries = []
        creditor_index = 0
        debtor_index = 0
        while creditor_index < len(creditors) and debtor_index < len(debtors):
            credit = creditors[creditor_index]
            debt = debtors[debtor_index]
            amount = min(credit["amount"], debt["amount"]).quantize(TWOPLACES, rounding=ROUND_HALF_UP)

            if amount > 0:
                entries.append(
                    {
                        "from_user_id": debt["user_id"],
                        "from_user_name": members[debt["user_id"]].name,
                        "to_user_id": credit["user_id"],
                        "to_user_name": members[credit["user_id"]].name,
                        "amount": amount,
                    }
                )

            credit["amount"] = self._q(credit["amount"] - amount)
            debt["amount"] = self._q(debt["amount"] - amount)

            if credit["amount"] == Decimal("0.00"):
                creditor_index += 1
            if debt["amount"] == Decimal("0.00"):
                debtor_index += 1

        return entries

    def _ensure_member(self, group: Group, current_user: User) -> None:
        if current_user.id not in {member.user_id for member in group.members}:
            raise PermissionError("You do not have access to this group")

    def _q(self, value: Decimal | float | int) -> Decimal:
        return Decimal(value).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
