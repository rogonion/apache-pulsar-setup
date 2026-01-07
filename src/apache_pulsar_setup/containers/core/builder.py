from apache_pulsar_setup.core import BaseBuilder, BuildahContainer, prune_cache_images, BuildSpec


class CoreBuilder(BaseBuilder):
    def __init__(self, config: BuildSpec, cache_prefix: str = ""):
        super().__init__(config, cache_prefix)
        self.image_name = f"{self.config.ProjectName}-core"
        self.image_tag = self.config.ApachePulsar.Version

    def _init_cache_prefix(self, cache_prefix: str):
        if len(cache_prefix) > 0:
            self.cache_prefix = cache_prefix
        else:
            self.cache_prefix = f"{self.config.ProjectName}/cache/core/{self.config.ApachePulsar.Version}"

    def build(self):
        self.log(f"Starting build for Apache Pulsar {self.config.ApachePulsar.Version} core", style="bold blue")

        current_step = 1
        total_no_of_steps = 4

        with BuildahContainer(
                base_image=self.config.BaseImage,
                image_name=self.image_name,
                config=self.config,
                cache_prefix=self.cache_prefix
        ) as container:
            self.log(
                f"[bold blue]Step {current_step}/{total_no_of_steps}[/bold blue]: Installing build dependencies (curl, tar)")

            container.run_cached(
                command=[
                    "sh", "-c",
                    f"""
                        zypper --non-interactive refresh &&
                        zypper --non-interactive install """ + " ".join(self.config.ApachePulsar.Build.Dependencies)],
                extra_cache_keys={"step": "deps", "packages": sorted(self.config.ApachePulsar.Build.Dependencies)}
            )

            current_step += 1
            self.log(
                f"[bold blue]Step {current_step}/{total_no_of_steps}[/bold blue]: Preparing directory {self.config.ApachePulsar.Prefix}")

            container.run(["mkdir", "-p", self.config.ApachePulsar.Prefix])

            current_step += 1
            self.log(
                f"[bold blue]Step {current_step}/{total_no_of_steps}[/bold blue]: Downloading and Extracting from {self.config.ApachePulsar.SourceUrl}")

            tar_path = f"/tmp/pulsar-{self.config.ApachePulsar.Version}.tar.gz"

            container.run_cached(
                command=[
                    "sh", "-c",
                    f"""
                            curl -L '{self.config.ApachePulsar.SourceUrl}' -o {tar_path} && 
                            tar -xzf {tar_path} -C {self.config.ApachePulsar.Prefix} --strip-components=1 &&
                            rm {tar_path}
                            """
                ],
                extra_cache_keys={
                    "step": "download_extract",
                    "url": self.config.ApachePulsar.SourceUrl,
                    "prefix": self.config.ApachePulsar.Prefix
                }
            )

            current_step += 1
            self.log(
                f"[bold blue]Step {current_step}/{total_no_of_steps}[/bold blue]: Verifying installation and committing.")

            try:
                pulsar_bin = f"{self.config.ApachePulsar.Prefix}/bin/pulsar"
                container.run(["test", "-x", pulsar_bin])

                self.log(f"Verification successful: Found {pulsar_bin}", style="bold green")
            except Exception:
                self.log("[bold red]Verification Failed[/bold red]: Pulsar binary missing in extraction path.")
                raise

            container.configure([
                ("--label", f"org.apache.pulsar.version={self.config.ApachePulsar.Version}"),
                ("--label", f"org.apache.pulsar.prefix={self.config.ApachePulsar.Prefix}"),
            ])

            image_name_tag = self.image_name + ":" + self.image_tag
            container.commit(image_name_tag)

            self.log(f"Image tagged as: [green]{image_name_tag}[/green]")

    def prune_cache_images(self):
        prune_cache_images(self.config.Buildah.Path, self.cache_prefix)