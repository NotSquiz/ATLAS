from qwen_tts.inference.qwen3_tts_model import Qwen3TTSModel

m = Qwen3TTSModel.from_pretrained('Qwen/Qwen3-TTS-12Hz-0.6B-Base')

print('generate_defaults:', m.generate_defaults)
print('model type:', type(m.model))

# Try to find the actual generate method
import inspect
for name, method in inspect.getmembers(m, predicate=inspect.ismethod):
    if 'generate' in name.lower():
        sig = inspect.signature(method)
        print(f"\n{name}{sig}")
