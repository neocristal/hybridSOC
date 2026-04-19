# HybridSOC Kafka Topic Configuration
# Run after Kafka is running: bash kafka/create-topics.sh

KAFKA_BROKER="localhost:9092"

echo "Creating HybridSOC Kafka topics..."

# SIEM alerts from Wazuh
kafka-topics.sh --create --bootstrap-server $KAFKA_BROKER \
  --topic soc-alerts \
  --partitions 6 \
  --replication-factor 1 \
  --config retention.ms=604800000  # 7 days

# Network events from Suricata/Zeek
kafka-topics.sh --create --bootstrap-server $KAFKA_BROKER \
  --topic network-events \
  --partitions 6 \
  --replication-factor 1

# Network flows (Zeek conn.log)
kafka-topics.sh --create --bootstrap-server $KAFKA_BROKER \
  --topic network-flows \
  --partitions 4 \
  --replication-factor 1

# API gateway access logs
kafka-topics.sh --create --bootstrap-server $KAFKA_BROKER \
  --topic api-logs \
  --partitions 3 \
  --replication-factor 1

# AI risk scoring results
kafka-topics.sh --create --bootstrap-server $KAFKA_BROKER \
  --topic ai-risk-scores \
  --partitions 3 \
  --replication-factor 1

# GRC compliance events
kafka-topics.sh --create --bootstrap-server $KAFKA_BROKER \
  --topic grc-events \
  --partitions 3 \
  --replication-factor 1

# SOAR incident actions
kafka-topics.sh --create --bootstrap-server $KAFKA_BROKER \
  --topic soar-actions \
  --partitions 3 \
  --replication-factor 1

echo "✅ All Kafka topics created"
kafka-topics.sh --list --bootstrap-server $KAFKA_BROKER
