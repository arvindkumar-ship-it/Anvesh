import sys
import types
provider = types.ModuleType('litellm')
def no_live_call(*args, **kwargs):
    raise RuntimeError('No live provider calls in offline tests')
provider.completion = no_live_call
sys.modules['litellm'] = provider
