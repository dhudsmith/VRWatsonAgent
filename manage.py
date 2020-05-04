import os, sys, argparse, subprocess, signal

# Project defaults
DEFAULT_IP = '0.0.0.0:3000'

class Command:
	def __init__(self, name, descr, runcmd, env={}):
		self.name = name
		self.descr = descr
		self.runcmd = runcmd
		self.env = env

	def run(self, conf):
		cmd = self.runcmd(conf)
		env = os.environ
		env.update(conf)
		env.update(self.env)
		subprocess.call(cmd, env=env, shell=True)

class CommandManager:
	def __init__(self):
		self.commands = {}

	def add(self, command):
		self.commands[command.name] = command

	def configure(self, conf):
		self.conf = conf

	def run(self, command):
		if command in self.commands:
			self.commands[command].run(self.conf)
		else:
			print("invalid command specified\n")
			print(self.availableCommands())

	def availableCommands(self):
		commands = sorted(self.commands.values(), key=lambda c: c.name)
		space = max([len(c.name) for c in commands]) + 2
		description = 'available subcommands:\n'
		for c in commands:
			description += '  ' + c.name + ' ' * (space - len(c.name)) + c.descr + '\n'
		return description

cm = CommandManager()

cm.add(Command(
	"build",
	"compiles python files in project into .pyc binaries",
	lambda c: 'python -m compileall .'))

cm.add(Command(
	'app',
	'runs server with flask_sockets for maintaining websocket connection to unity app',
	lambda c: 'python server/routes/app.py',
	{
		'FLASK_SOCKETS': 'true'
	}
))

