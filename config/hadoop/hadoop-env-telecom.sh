
# ====================================================================
# TELECOM MAPREDUCE RESOURCE-CONSTRAINED SINGLE-NODE CONFIGURATION
# ====================================================================
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export HADOOP_HOME=/opt/hadoop
export HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
export HADOOP_LOG_DIR=/var/log/hadoop

# Conservative JVM Heap Allocations
export HADOOP_HEAPSIZE_MAX=1024m
export HDFS_NAMENODE_OPTS="-Xms256m -Xmx512m $HADOOP_NAMENODE_OPTS"
export HDFS_DATANODE_OPTS="-Xms256m -Xmx512m $HADOOP_DATANODE_OPTS"
