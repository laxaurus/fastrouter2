# FastRouter OSS

Open-source LLM routing core for Chinese AI providers. Part of the [FastRouter](https://fastrouter.dev) platform.

## What This Is

A pre-configured LiteLLM proxy setup with:
- **DeepSeek** (deepseek-chat, deepseek-reasoner)
- **Qwen** (qwen-plus, qwen-max, qwen-turbo)
- Automatic failover between providers
- Circuit breaker pattern
- OpenAI-compatible API

## Quickstart

```bash
# Set your provider API keys
export DEEPSEEK_API_KEY=sk-your-key
export QWEN_API_KEY=sk-your-key

# Generate config
cd litellm && python generate_config.py

# Start
docker compose -f docker/docker-compose.yml up
```

Your proxy is now running at `http://localhost:4000/v1/chat/completions`.

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-master-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-chat", "messages": [{"role": "user", "content": "Hello"}]}'
```

## Providers

| Provider | Models | Failover |
|----------|--------|----------|
| DeepSeek | chat, reasoner | → Qwen |
| Qwen | plus, max, turbo | → DeepSeek |

## Adding Providers

Edit `litellm/config.template.yaml` and add a new entry:

```yaml
- model_name: your-model
  litellm_params:
    model: openai/your-model
    api_base: https://your-provider.com/v1
    api_key: os.environ/YOUR_API_KEY
```

Add a fallback in `router_settings.fallbacks`.

## License

MIT — use it, fork it, build on it.
