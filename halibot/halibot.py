#
# Main bot class
#    Handles routing, config, agent/module loading
#
import json
import threading
import os, sys
from importlib.machinery import SourceFileLoader
from queue import Queue,Empty
from .halmodule import HalModule
from .halagent import HalAgent
from .halauth import HalAuth
from .loader import Loader

# Avoid appending "." if it i
if "." not in sys.path:
	sys.path.append(".")
import logging

class ObjectDict(dict):
	def __getattr__(self, key):
		if key == "modules":
			return dict(filter(lambda x: isinstance(x[1], HalModule), self.items()))
		elif key == "agents":
			return dict(filter(lambda x: isinstance(x[1], HalAgent), self.items()))
		return super.__getattr__(self, key)


class Halibot():

	config = {}

	running = False
	log = None

	def __init__(self, **kwargs):
		self.log = logging.getLogger(self.__class__.__name__)

		self.use_config = kwargs.get("use_config", True)
		self.use_auth = kwargs.get("use_auth", True)

		self.auth = HalAuth()
		self.objects = ObjectDict()

	# Start the Hal instance
	def start(self, block=True):
		self.running = True

		if self.use_config:
			self._load_config()
			self._instantiate_agents()
			self._instantiate_modules()
			if self.use_auth:
				self.auth.load_perms(self.config.get("auth-path","permissions.json"))

	def shutdown(self):
		self.log.info("Shutting down halibot...");

		for o in self.objects.values():
			o._shutdown()

		self.log.info("Halibot shutdown. Threads left: " + str(threading.active_count()))

	def add_agent_instance(self, name, inst):
		self.objects[name] = inst
		inst.name = name
		inst.init()
		self.log.info("Instantiated agent '" + name + "'")

	def add_module_instance(self, name, inst):
		self.objects[name] = inst
		inst.name = name
		inst.init()
		self.log.info("Instantiated module '" + name + "'")

	def _load_config(self):
		with open("config.json","r") as f:
			self.config = json.loads(f.read())

			# Deprecated; remove with 1.0
			self.agent_loader = Loader(self.config["package-path"], HalAgent)
			self.module_loader = Loader(self.config["package-path"], HalModule)


	def _get_class_from_package(self, pkgname, clsname):
		pkg = self.get_package(pkgname)
		if pkg == None:
			self.log.error("Cannot find package {}!".format(pkgname))
			return None

		obj = getattr(pkg, clsname, None)
		if obj == None:
			self.log.error("Cannot find class {} in package {}!".format(clsname, pkgname))
			return None

		return obj

	def _instantiate_agents(self):
		inst = self.config["agent-instances"]

		for k in inst.keys():
			# TODO include directive

			conf = inst[k]
			split = conf["of"].split(":")

			if len(split) == 1:
				# deprecated; remove with 1.0
				obj = self.agent_loader.get(conf["of"])
			elif len(split) == 2:
				obj = self._get_class_from_package(split[0], split[1])
			else:
				self.log.error("Invalid class identifier {}, must contain only 1 ':'".format(conf["of"]))
				continue

			self.add_agent_instance(k, obj(self, conf))

	def _instantiate_modules(self):
		inst = self.config["module-instances"]

		for k in inst.keys():
			# TODO include directive

			conf = inst[k]
			split = conf["of"].split(":")

			if len(split) == 1:
				# deprecated; remove with 1.0
				obj = self.module_loader.get(conf["of"])
			elif len(split) == 2:
				obj = self._get_class_from_package(split[0], split[1])
			else:
				self.log.error("Invalid class identifier {}, must contain only 1 ':'".format(conf["of"]))
				continue

			self.add_module_instance(k, obj(self, conf))

	def get_object(self, name):
		return self.objects.get(name, None)

	def get_package(self, name):
		for prefix in self.config['package-path']:
			path = os.path.join(prefix, name, '__init__.py')
			if os.path.exists(path):
				return SourceFileLoader(path, path).load_module()
		return None

	# TODO: Reload a class, and restart all modules of that class
	def reload(self, cls):
		pass

	# Restart a module instance by name
	def restart(self, name):
		o = self.get_object(name)
		if o:
			o.shutdown()
			o.init()
		else:
			self.log.warning("Failed to restart instance '{}'".format(name))
