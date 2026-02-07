from Objects.Items.Swords.swordBaseClass import Sword


class ShortSword(Sword):
	def __init__(self, reach: int, **kwargs) -> None:
		super().__init__(**kwargs)
		self.reach: int = reach

	def object_type(self) -> str:
		return "Short Sword"
