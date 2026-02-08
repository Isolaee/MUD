"""Short sword — a light, one-handed melee weapon.

Short swords are fast bladed weapons with limited reach,
suitable for close-quarters combat.
"""

from Objects.Items.Swords.swordBaseClass import Sword


class ShortSword(Sword):
	"""A short, one-handed sword.

	Attributes:
		reach: Maximum attack range in tiles.
	"""

	def __init__(self, reach: int, **kwargs) -> None:
		super().__init__(**kwargs)
		self.reach: int = reach

	def object_type(self) -> str:
		return "Short Sword"
