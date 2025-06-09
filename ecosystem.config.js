module.exports = {
  apps: [{
    name: 'motion-detection',
    script: 'python3',
    args: 'main.py',
    cwd: '/app',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      PYTHONPATH: '/app'
    },
    error_file: '/app/logs/motion-detection-error.log',
    out_file: '/app/logs/motion-detection-out.log',
    log_file: '/app/logs/motion-detection.log',
    time: true,
    max_restarts: 10,
    min_uptime: '10s'
  }]
};
