"""Sword base class — a concrete melee weapon category.

Swords inherit all weapon combat attributes and can be further
specialised into sub-types (ShortSword, LongSword, etc.).
"""

from Objects.Items.weapons import Weapon


class Sword(Weapon):
	"""A bladed melee weapon.

	Inherits attack bonus, hit chance, and damage type from Weapon.
	Subclasses add reach, weight, or other sword-specific attributes.
	"""

	def object_type(self) -> str:
		return "Sword"

	def get_name(self) -> str:
		"""Return the display name of this sword."""
		return self.name
