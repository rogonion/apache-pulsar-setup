from pathlib import Path

from apache_pulsar_setup.core import BaseBuilder, BuildSpec, prune_cache_images, BuildahContainer


class RuntimeBuilder(BaseBuilder):
    def __init__(self, config: BuildSpec, cache_prefix: str = "", image_name: str = "", image_tag: str = ""):
        super().__init__(config, cache_prefix)

        if len(image_name) > 0:
            self.image_name = image_name
        else:
            self.image_name = f"{self.config.ProjectName}-runtime"

        if len(image_tag) > 0:
            self.image_tag = image_tag
        else:
            self.image_tag = self.config.ApachePulsar.Version

    def _init_cache_prefix(self, cache_prefix: str):
        if len(cache_prefix) > 0:
            self.cache_prefix = cache_prefix
        else:
            self.cache_prefix = f"{self.config.ProjectName}/cache/runtime/{self.config.ApachePulsar.Version}"

    def build(self):
        self.log(f"Starting build for Apache Pulsar {self.config.ApachePulsar.Version} runtime",
                 style="bold blue")

        current_step = 1

        with BuildahContainer(
                base_image=self.config.BaseImage,
                image_name=self.image_name,
                config=self.config,
                cache_prefix=self.cache_prefix
        ) as container:
            self.log(f"[bold blue]Step {current_step}[/bold blue]: Retrieving apache pulsar artifacts")

            self.image_tag = self.config.ApachePulsar.Version

            container.copy_container_current(
                f"{self.config.ProjectName}-core:{self.config.ApachePulsar.Version}",
                self.config.ApachePulsar.Prefix,
                self.config.ApachePulsar.Prefix
            )

            current_step += 1
            self.log(
                f"[bold blue]Step {current_step}[/bold blue]: Installing apache pulsar runtime dependencies")

            container.run_cached(
                command=[
                    "sh", "-c",
                    f"""
                        zypper --non-interactive refresh &&
                        zypper --non-interactive install """ + " ".join(self.config.ApachePulsar.Runtime.Dependencies)],
                extra_cache_keys={"step": "deps", "packages": sorted(self.config.ApachePulsar.Runtime.Dependencies)}
            )

            container.run(command=["zypper", "clean", "--all"])

            container.install_jdk_jre(
                self.config.ApachePulsar.Runtime.Java.Jre.Major,
                self.config.ApachePulsar.Runtime.Java.Jre.Minor,
                self.config.ApachePulsar.Runtime.Java.Jre.Build,
                component="jre"
            )

            current_step += 1
            self.log(
                f"[bold blue]Step {current_step}[/bold blue]: Setting up system user")

            container.run(
                command=["groupadd", "-r", "-g", str(self.config.ApachePulsar.Runtime.Gid), "pulsar"]
            )

            container.run(
                command=["useradd", "-r", "-u", str(self.config.ApachePulsar.Runtime.Uid), "-g",
                         str(self.config.ApachePulsar.Runtime.Gid), "-d", self.config.ApachePulsar.Prefix, "-s",
                         "/sbin/nologin", "-c",
                         '"Apache Pulsar Server"', "pulsar"]
            )

            container.configure(
                [
                    ("--label", f"io.apache.pulsar.user.uid={self.config.ApachePulsar.Runtime.Uid}"),
                    ("--label", f"io.apache.pulsar.user.gid={self.config.ApachePulsar.Runtime.Gid}"),
                    ("--label", f"io.apache.pulsar.user.name=pulsar"),
                ]
            )

            current_step += 1
            self.log(
                f"[bold blue]Step {current_step}[/bold blue]: Setting up directories & permissions")

            container.configure([
                ("--env",
                 f"PATH={self.config.ApachePulsar.Prefix}/bin:/opt/java/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"),
                ("--env", f"PULSAR_HOME={self.config.ApachePulsar.Prefix}"),
                ("--env", "LANG=C.UTF-8"),
                ("--env", "LC_ALL=C.UTF-8")
            ])

            for d in ["data", "logs"]:
                full_d_dir = f"{self.config.ApachePulsar.Prefix}/{d}"
                container.run(["mkdir", "-p", full_d_dir])
                container.configure([
                    ("--volume", full_d_dir)
                ])

            container.run(
                command=["chown", "-R",
                         f"{self.config.ApachePulsar.Runtime.Uid}:{self.config.ApachePulsar.Runtime.Gid}",
                         self.config.ApachePulsar.Prefix]
            )

            container.copy_host_container(Path(f"{self.config.ApachePulsar.Runtime.Resources}/entrypoint.sh"),
                                          "/usr/local/bin/entrypoint.sh")
            container.run(command=["chmod", "+x", "/usr/local/bin/entrypoint.sh"])

            container.configure([
                ("--entrypoint", '["/usr/local/bin/entrypoint.sh"]'),
                ("--cmd", '["pulsar", "standalone"]'),
                ("--user", str(self.config.ApachePulsar.Runtime.Uid)),
                ("--port", "6650"),
                ("--port", "8080")
            ])

            current_step += 1
            self.log(
                f"[bold blue]Step {current_step}[/bold blue]: Tagging image and adding metadata.")

            container.configure([
                ("--label", f"org.apache.pulsar.version={self.config.ApachePulsar.Version}"),
                ("--label", f"org.apache.pulsar.prefix={self.config.ApachePulsar.Prefix}"),
            ])
            image_name_tag = self.image_name + ":" + self.image_tag
            container.commit(image_name_tag)

            self.log(f"Image tagged as: [green]{image_name_tag}[/green]")


    def prune_cache_images(self):
        prune_cache_images(self.config.Buildah.Path, self.cache_prefix)
