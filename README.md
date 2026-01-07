# apache-pulsar-setup

A utility for creating a customized, rootless [Apache Pulsar](https://pulsar.apache.org/) container image. This project builds a "lean" image based on the official binary distribution, decoupled from the heavy JDK layers found in standard images.

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

VOLUME="pulsar-data"
IMAGE="localhost/apache-pulsar:4.0.0"

# Create volume if it doesn't exist
podman volume exists $VOLUME || podman volume create $VOLUME

# Ensure permissions match the container user (1002)
podman unshare chown -R $CONTAINER_UID:$CONTAINER_GID $(podman volume inspect $VOLUME --format '{{.Mountpoint}}')

podman run -d \
        --name $CONTAINER \
        --network $NETWORK \
        --network-alias $NETWORK_ALIAS \
        --user $CONTAINER_UID:$CONTAINER_GID \
        -p $PORT_BINARY:6650 \
        -p $PORT_HTTP:8080 \
        -v $VOLUME:/usr/local/pulsar/data \
        -e "PULSAR_MEM=-Xms512m -Xmx512m -XX:MaxDirectMemorySize=1g" \
        -e "PULSAR_GC=-XX:+UseG1GC -XX:MaxGCPauseMillis=10" \
        -e "PULSAR_PREFIX_advertisedAddress=localhost" \
        $IMAGE
```

## Application Container Image Features

### Ports

<table> <thead> <th>Port</th> <th>Purpose</th> </thead> <tbody> <tr> <td><code>6650</code></td> <td><strong>Pulsar Binary Protocol.</strong> Used by clients (Go, Java, Python) to produce/consume messages.</td> </tr> <tr> <td><code>8080</code></td> <td><strong>HTTP / Admin API.</strong> Used for the Admin REST API and WebSocket clients.</td> </tr> </tbody> </table>

### Volumes

<table> <thead> <th>Path</th> <th>Purpose</th> </thead> <tbody> <tr> <td><code>/usr/local/pulsar/data</code></td> <td><strong>Data Directory.</strong> Stores BookKeeper ledgers (messages) and ZooKeeper snapshots (metadata). <strong>Critical:</strong> Ensure you mount a volume here to persist data across restarts.</td> </tr> <tr> <td><code>/usr/local/pulsar/logs</code></td> <td><strong>Logs Directory.</strong> Stores Garbage Collection logs and server logs. Optional mount.</td> </tr> </tbody> </table>


### Environment variables

Configuration is handled via environment variables passed at runtime.

<table> <thead> <th>Name</th> <th>Example</th> <th>Purpose</th> </thead> <tbody> <tr> <td><code>PULSAR_MEM</code></td> <td><code>-Xms512m -Xmx512m -XX:MaxDirectMemorySize=1g</code></td> <td>JVM Heap and Direct Memory settings. Critical for tuning performance vs resource usage.</td> </tr> <tr> <td><code>PULSAR_GC</code></td> <td><code>-XX:+UseG1GC</code></td> <td>Garbage Collection flags. Recommended to use G1GC or ZGC for Java 21+.</td> </tr> <tr> <td><code>PULSAR_PREFIX_[Config]</code></td> <td><code>PULSAR_PREFIX_advertisedAddress=localhost</code></td> <td><strong>Config Override.</strong> Any variable starting with <code>PULSAR_PREFIX_</code> will override the corresponding setting in <code>standalone.conf</code> or <code>broker.conf</code>.</td> </tr> </tbody> </table>