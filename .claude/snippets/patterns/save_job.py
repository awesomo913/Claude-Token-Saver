# From: sessions/ClaudeProjects/my_claude_project_ai/local_relay/local_relay/job_config.py:243

def save_job(config):
    config_path = os.path.join(JOBS_DIR, config["job_id"], "config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
