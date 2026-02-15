"""Dagger — a light, fast melee weapon.

Daggers are small bladed weapons with short reach,
ideal for quick strikes in close combat.
"""

from Objects.Items.weapons import Weapon


class Dagger(Weapon):
	"""A small bladed weapon.

	Attributes:
		reach: Maximum attack range in tiles.
	"""

	def __init__(self, reach: int, **kwargs) -> None:
		super().__init__(**kwargs)
		self.reach: int = reach

	def object_type(self) -> str:
		return "Dagger"
