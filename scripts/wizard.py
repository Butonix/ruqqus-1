#Ruqqus installation wizard
import pip
import os
import venv

print('   /\\')
print(' _/__\\_')
print(' ╭───────╮')
print('╭┤  ╹ ╹  ├╮')
print(' ╰─┬───┬─╯')
print("")
print("Welcome. I am the Ruqqus Installation and Setup Wizard.")
print("I will guide you through the process of setting up your own Ruqqus server.")

#navigate to folder above ruqqus repo
path=os.path.realpath('.')
if path.endswith("scripts"):
	path=os.path.realpath(path+"/..")
if path.endswith("ruqqus"):
	path=os.path.realpath(path+"/..")


print("First, I will create a virtual Python environment for Ruqqus to run in.")
print("This pocket universe will contain everything Ruqqus needs.")
print("This will be created at:")
print(f"{path}/venv")

input("Press enter to continue.")

os.system(f"python -m venv {path}/venv")