# Test core halibot functionality

import time
import util
import halibot
import unittest

class StubModule(halibot.HalModule):
	inited = False
	received = []

	def init(self):
		self.inited = True

	def receive(self, msg):
		self.received.append(msg)

class StubAgent(halibot.HalAgent):
	inited = False

	def init(self):
		self.inited = True

class TestCore(util.HalibotTestCase):

	def test_add_module(self):
		stub = StubModule(self.bot)
		self.bot.add_module_instance('stub_mod', stub)

		self.assertTrue(stub.inited)
		self.assertEqual(stub, self.bot.get_object('stub_mod'))

	def test_add_agent(self):
		stub = StubAgent(self.bot)
		self.bot.add_agent_instance('stub_agent', stub)

		self.assertTrue(stub.inited)
		self.assertEqual(stub, self.bot.get_object('stub_agent'))

	def test_send_recv(self):
		agent = StubAgent(self.bot)
		mod = StubModule(self.bot)
		self.bot.add_agent_instance('stub_agent', agent)
		self.bot.add_module_instance('stub_mod', mod)

		foo = halibot.Message(body='foo')
		bar = halibot.Message(body='bar')
		baz = halibot.Message(body='baz', origin='glub_agent')

		agent.connect(mod)
		agent.dispatch(foo)
		agent.send_to(bar, [ 'stub_mod' ])
		agent.dispatch(baz)

		# TODO do something sensible here
		timeout = 10
		increment = .1
		while timeout > 0 and len(mod.received) != 3:
			time.sleep(increment)
			timeout -= increment

		self.assertEqual(3, len(mod.received))
		self.assertEqual(foo.body, mod.received[0].body)
		self.assertEqual(bar.body, mod.received[1].body)
		self.assertEqual(baz.body, mod.received[2].body)
		self.assertEqual('stub_mod', mod.received[0].target)
		self.assertEqual('stub_mod', mod.received[1].target)
		self.assertEqual('stub_mod', mod.received[2].target)
		self.assertEqual('stub_agent', mod.received[0].origin)
		self.assertEqual('stub_agent', mod.received[1].origin)
		self.assertEqual('glub_agent', mod.received[2].origin)

if __name__ == '__main__':
	unittest.main()

