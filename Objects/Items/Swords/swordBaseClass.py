from Objects.Items import Weapon


class Sword(Weapon):
	def object_type(self) -> str:
		return "Sword"

	def get_name(self) -> str:
		return self.name
