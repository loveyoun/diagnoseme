cat > /usr/local/etc/redis/redis.conf <<EOF
bind 0.0.0.0
requirepass ${REDIS_PASSWORD}
port ${REDIS_PORT}
EOF

redis-server /usr/local/etc/redis/redis.conf