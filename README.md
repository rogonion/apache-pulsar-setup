# apache-pulsar-setup

A utility for creating a customized, rootless [Apache Pulsar](https://pulsar.apache.org/) container image. This project
builds a "lean" image based on the official binary distribution, decoupled from the heavy JDK layers found in standard
images.

**Base Image:** [openSUSE Leap 16.0](https://registry.opensuse.org/cgi-bin/cooverview)  
**Apache Pulsar Version:** 4.0.0 (Official Binary Release)

## Pre-requisites

**OS:** Linux-based.

<table>
    <caption>Required Tools</caption>
    <thead>
        <tr>
            <th>Package</th>
            <th>Version</th>
            <th>Notes</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Python</td>
            <td>3.13+</td>
            <td>
                <p>Core language the CLI tool is written in.</p>
            </td>
        </tr>
        <tr>
            <td><a href="https://python-poetry.org/docs/">Poetry</a></td>
            <td>2.2.1+</td>
            <td>
                <p>Project dependency manager.</p>
            </td>
        </tr>
        <tr>
            <td><a href="https://buildah.io/">Buildah</a></td>
            <td>1.41.5+</td>
            <td>
                <p>Used to programmatically create OCI-compliant container images without a daemon.</p>
            </td>
        </tr>
        <tr>
            <td><a href="https://taskfile.dev/">Taskfile</a></td>
            <td>3.46.3+</td>
            <td>
                <p>Optional. You can use the provided <a href="taskw">shell script wrapper</a> (<code>./taskw</code>) which scopes the binary to the project.</p>
            </td>
        </tr>
    </tbody>
</table>

## Usage

List available tasks:

```shell
TASKFILE_BINARY="./taskw"

$TASKFILE_BINARY --list
```

Setup python virtual environment and install dependencies:

```shell
TASKFILE_BINARY="./taskw"

$TASKFILE_BINARY init
```

View CLI tool options and build help:

```shell
TASKFILE_BINARY="./taskw"

$TASKFILE_BINARY run -- --help
```

### Example

Build the core artifact (downloads and extracts the Pulsar distribution):

```shell
TASKFILE_BINARY="./taskw"

$TASKFILE_BINARY run -- containers core build
```

Build the runtime image (installs Java 21, sets up users, and copies artifacts):

```shell
TASKFILE_BINARY="./taskw"

$TASKFILE_BINARY run -- containers runtime build
```

Run the built container using `podman`:

- Temporary container, does not work well between restarts with persistence.
    ```shell
    #!/bin/bash
    
    CONTAINER="pulsar4.0.0"
    NETWORK="tumbleweed"
    NETWORK_ALIAS="pulsar-standalone"
    CONTAINER_UID=1002
    CONTAINER_GID=1002
    
    # Ports: 6650 (Binary), 8080 (HTTP/Admin)
    PORT_BINARY=6650
    PORT_HTTP=8080
    
    IMAGE="localhost/apache-pulsar:4.0.0"
    
    podman run -d \
            --name $CONTAINER \
            --network $NETWORK \
            --network-alias $NETWORK_ALIAS \
            --user $CONTAINER_UID:$CONTAINER_GID \
            -p $PORT_BINARY:6650 \
            -p $PORT_HTTP:8080 \
            -e "PULSAR_MEM=-Xms512m -Xmx512m -XX:MaxDirectMemorySize=1g" \
            -e "PULSAR_GC=-XX:+UseG1GC -XX:MaxGCPauseMillis=10" \
            -e "PULSAR_PREFIX_advertisedAddress=localhost" \
            $IMAGE
    ```
- 3 separate nodes (zookeeper->bookie->broker) for persistence:

  You can find the pre-populated configuration files inside the runtime image at `$PULSAR_HOME/conf/`. Extract them (
  zookkeeper.conf, bookkeeper.conf, and broker.conf) to the directory where your script for running the container shall
  be.

  For zookeeper, nothing much needs to change but for `bookie` and `brooker` some snippets need to be edited in the
  config files so that they can talk to each other as well as other services can talk to them...

  `bookkeeper.conf`:
  ```toml
  # CONNECTIVITY
  # 1. The Port: Must be 3181 (Not 6650, that is for Brokers)
  bookiePort=3181
  
  # 2. The Identity: This MUST match your Podman '--network-alias' for the bookie.
  # If this is wrong, the Broker will try to connect to a random container ID and fail.
  advertisedAddress=pulsar_bookie
  
  # 3. Security: Allow binding to loopback in containers
  allowLoopback=true
  
  # METADATA (MUST MATCH INIT COMMAND)
  # 4. The Chroot: Notice the '/ledgers' at the end.
  # If this is missing, you get "BookKeeper cluster not initialized"
  metadataServiceUri=metadata-store:zk:pulsar_zookeeper:2181/ledgers
  
  # 5. Legacy Fallback: Keep this in sync with the URI above
  zkServers=pulsar_zookeeper:2181/ledgers
  ```

  `broker.conf`:
  ```toml
  # CLUSTER IDENTITY (MUST MATCH INIT COMMAND)
  # 1. Cluster Name: If this doesn't match, the broker will refuse to start.
  clusterName=tumbleweed
  
  # 2. Global ZK: Brokers use the ROOT for tenant/namespace configuration.
  # (Note: No '/ledgers' here usually, unless you chrooted the whole cluster)
  zookeeperServers=pulsar_zookeeper:2181
  configurationStoreServers=pulsar_zookeeper:2181
  
  # 3. Bookie Discovery: Brokers look for Bookies here.
  # MUST match the Bookie's 'metadataServiceUri'
  bookkeeperMetadataServiceUri=metadata-store:zk:pulsar_zookeeper:2181/ledgers
  
  # NETWORK (The Dual Listener)
  # 4. Access: Define 'internal' (for Trino/Bookie) and 'external' (for You/Go)
  advertisedListeners=internal:pulsar://broker:6650,external:pulsar://localhost:6650
  
  # 5. Routing: Tell the broker to use 'internal' for talking to other components
  internalListenerName=internal
  
  # STORAGE QUORUMS (Single Node Mode)
  # 6. Safety Checks: Since you only have 1 Bookie, you must force these to 1.
  # Defaults are 2 or 3, which will cause the Broker to crash loop.
  managedLedgerDefaultEnsembleSize=1
  managedLedgerDefaultWriteQuorum=1
  managedLedgerDefaultAckQuorum=1
  ```
  Once the configuration files are set, you can run the images (zookeeeper->init cluster->bookkeeper->broker):

  ```shell
  # 1. Start zookeeper

  CONTAINER="pulsar_zookeeper"
  NETWORK="tumbleweed"
  NETWORK_ALIAS="pulsar_zookeeper"
  CONTAINER_UID=1002
  CONTAINER_GID=1002
  VOLUME="pulsar_zookeeper"
  SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
  CONFIG_FILE=$SCRIPT_DIR/zookeeper.conf # Custom configuration file (COPY FROM runtime image)
  IMAGE="localhost/apache-pulsar:4.0.0"
  CMD="pulsar zookeeper"
  
  # PORT: 2181
  
  podman volume exists $VOLUME || podman volume create $VOLUME
  
  podman unshare chown -R $CONTAINER_UID:$CONTAINER_GID $(podman volume inspect $VOLUME --format '{{.Mountpoint}}')
  
  
  podman run -d \
    --name $CONTAINER \
    --network $NETWORK \
    --network-alias $NETWORK_ALIAS \
    --user $CONTAINER_UID:$CONTAINER_GID \
    -v $VOLUME:/usr/local/pulsar/data \
    -v $CONFIG_FILE:/usr/local/pulsar/conf/zookeeper.conf:ro,Z \
    -e "PULSAR_MEM=-Xms512m -Xmx512m -XX:MaxDirectMemorySize=1g" \
    -e "PULSAR_GC=-XX:+UseG1GC -XX:MaxGCPauseMillis=10" \
    $IMAGE \
    $CMD
  
  # 2. Initialize clust metadata (only once)
  NETWORK="tumbleweed"
  CLUSTER_NAME="tumbleweed"
  ZOOKEEPER="pulsar_zookeeper:2181"
  BROKER_WEB_URL="http://pulsar_zookeeper:8080"
  BROKER_SERVICE_URL="pulsar_broker:6650"
  IMAGE="localhost/apache-pulsar:4.0.0"
  
  podman run --rm \
  --network $NETWORK \
  $IMAGE \
  pulsar initialize-cluster-metadata \
    --cluster $CLUSTER_NAME \
    --zookeeper $ZOOKEEPER/ledgers \
    --configuration-store $ZOOKEEPER \
    --web-service-url $BROKER_WEB_URL \
    --broker-service-url $BROKER_SERVICE_URL
  
  # 3. Start bookie
  CONTAINER="pulsar_bookie"
  NETWORK="tumbleweed"
  NETWORK_ALIAS="pulsar_bookie"
  CONTAINER_UID=1002
  CONTAINER_GID=1002
  VOLUME="pulsar_bookie"
  SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
  CONFIG_FILE=$SCRIPT_DIR/bookkeeper.conf # Custom configuration file
  IMAGE="localhost/apache-pulsar:4.0.0"
  CMD="pulsar bookie"
  
  podman volume exists $VOLUME || podman volume create $VOLUME
  
  podman unshare chown -R $CONTAINER_UID:$CONTAINER_GID $(podman volume inspect $VOLUME --format '{{.Mountpoint}}')
  
  
  podman run -d \
    --name $CONTAINER \
    --network $NETWORK \
    --network-alias $NETWORK_ALIAS \
    --user $CONTAINER_UID:$CONTAINER_GID \
    -v $VOLUME:/usr/local/pulsar/data \
    -v $CONFIG_FILE:/usr/local/pulsar/conf/bookkeeper.conf:ro,Z \
    -e "PULSAR_MEM=-Xms512m -Xmx512m -XX:MaxDirectMemorySize=1g" \
    -e "PULSAR_GC=-XX:+UseG1GC -XX:MaxGCPauseMillis=10" \
    $IMAGE \
    $CMD
  
  # 4. Start broker
  CONTAINER="pulsar_broker"
  NETWORK="tumbleweed"
  NETWORK_ALIAS="pulsar_broker"
  CONTAINER_UID=1002
  CONTAINER_GID=1002
  VOLUME="pulsar_broker"
  SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
  CONFIG_FILE=$SCRIPT_DIR/broker.conf # Custom configuration file
  IMAGE="localhost/apache-pulsar:4.0.0"
  CMD="pulsar broker"
  
  podman volume exists $VOLUME || podman volume create $VOLUME
  
  podman unshare chown -R $CONTAINER_UID:$CONTAINER_GID $(podman volume inspect $VOLUME --format '{{.Mountpoint}}')
  
  
  podman run -d \
    --name $CONTAINER \
    --network $NETWORK \
    --network-alias $NETWORK_ALIAS \
    --user $CONTAINER_UID:$CONTAINER_GID \
    -v $VOLUME:/usr/local/pulsar/data \
    -v $CONFIG_FILE:/usr/local/pulsar/conf/broker.conf:ro,Z \
    -e "PULSAR_MEM=-Xms512m -Xmx512m -XX:MaxDirectMemorySize=1g" \
    -e "PULSAR_GC=-XX:+UseG1GC -XX:MaxGCPauseMillis=10" \
    $IMAGE \
    $CMD
  ```

## Application Container Image Features

### Ports

<table> <thead> <th>Port</th> <th>Purpose</th> </thead> <tbody> <tr> <td><code>6650</code></td> <td><strong>Pulsar Binary Protocol.</strong> Used by clients (Go, Java, Python) to produce/consume messages.</td> </tr> <tr> <td><code>8080</code></td> <td><strong>HTTP / Admin API.</strong> Used for the Admin REST API and WebSocket clients.</td> </tr> </tbody> </table>

### Volumes

<table> <thead> <th>Path</th> <th>Purpose</th> </thead> <tbody> <tr> <td><code>/usr/local/pulsar/data</code></td> <td><strong>Data Directory.</strong> Stores BookKeeper ledgers (messages) and ZooKeeper snapshots (metadata). <strong>Critical:</strong> Ensure you mount a volume here to persist data across restarts.</td> </tr> <tr> <td><code>/usr/local/pulsar/logs</code></td> <td><strong>Logs Directory.</strong> Stores Garbage Collection logs and server logs. Optional mount.</td> </tr> </tbody> </table>

### Environment variables

Configuration is handled via environment variables passed at runtime.

<table> <thead> <th>Name</th> <th>Example</th> <th>Purpose</th> </thead> <tbody> <tr> <td><code>PULSAR_MEM</code></td> <td><code>-Xms512m -Xmx512m -XX:MaxDirectMemorySize=1g</code></td> <td>JVM Heap and Direct Memory settings. Critical for tuning performance vs resource usage.</td> </tr> <tr> <td><code>PULSAR_GC</code></td> <td><code>-XX:+UseG1GC</code></td> <td>Garbage Collection flags. Recommended to use G1GC or ZGC for Java 21+.</td> </tr> <tr> <td><code>PULSAR_PREFIX_[Config]</code></td> <td><code>PULSAR_PREFIX_advertisedAddress=localhost</code></td> <td><strong>Config Override.</strong> Any variable starting with <code>PULSAR_PREFIX_</code> will override the corresponding setting in <code>standalone.conf</code> or <code>broker.conf</code>.</td> </tr> </tbody> </table>