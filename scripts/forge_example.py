from mdf_forge.forge import Forge
# You don't have to use the name "mdf" but we do for consistency.
mdf = Forge("mdf-test")

res = mdf.search("Sameh Tawfick_UIUC")

print(str(res))