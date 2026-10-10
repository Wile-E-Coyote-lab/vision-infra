2026-10-10 06:58:55.352Z: Host information
2026-10-10 06:58:55.352Z: ----------------
2026-10-10 06:58:55.352Z: OS: Ubuntu 22.04.5 LTS (stable release)
2026-10-10 06:58:55.353Z: Image details: https://github.com/github/codespaces-host-images/blob/main/README.md
2026-10-10 06:58:55.353Z: ----------------

=================================================================================
2026-10-10 06:58:55.355Z: Configuration starting...
2026-10-10 06:58:55.371Z: Cloning...

=================================================================================
2026-10-10 06:58:56.618Z: Creating container...
2026-10-10 06:58:56.670Z: $ devcontainer up --id-label Type=codespaces --workspace-folder /var/lib/docker/codespacemount/workspace/vision-infra --mount type=bind,source=/.codespaces/agent/mount/cache,target=/vscode --user-data-folder /var/lib/docker/codespacemount/.persistedshare --container-data-folder .vscode-remote/data/Machine --container-system-data-folder /var/vscode-remote --log-level trace --log-format json --update-remote-user-uid-default never --mount-workspace-git-root false --omit-config-remote-env-from-metadata --skip-non-blocking-commands --skip-post-create --config "/var/lib/docker/codespacemount/workspace/vision-infra/.devcontainer/devcontainer.json" --override-config /root/.codespaces/shared/merged_devcontainer.json --default-user-env-probe loginInteractiveShell --container-session-data-folder /workspaces/.codespaces/.persistedshare/devcontainers-cli/cache --secrets-file /root/.codespaces/shared/user-secrets-envs.json
2026-10-10 06:58:56.815Z: @devcontainers/cli 0.83.3. Node.js v18.20.8. linux 6.8.0-1064-azure x64.
2026-10-10 06:58:57.015Z: Resolving Feature dependencies for 'ghcr.io/devcontainers/features/terraform:1'...
2026-10-10 06:58:57.543Z: Resolving Feature dependencies for 'ghcr.io/devcontainers/features/docker-in-docker:2'...
2026-10-10 06:58:57.817Z: Resolving Feature dependencies for 'ghcr.io/devcontainers/features/github-cli:1'...
2026-10-10 06:58:58.203Z: Resolving Feature dependencies for 'ghcr.io/dhoeric/features/google-cloud-cli:1'...
2026-10-10 06:58:58.599Z: Files to omit: ''
2026-10-10 06:58:58.765Z: Resolving Feature dependencies for 'ghcr.io/devcontainers/features/github-cli:1'...
2026-10-10 06:58:59.145Z: Soft-dependency 'ghcr.io/devcontainers/features/common-utils' is not required.  Removing from installation order...
2026-10-10 06:58:59.145Z: Soft-dependency 'ghcr.io/devcontainers/features/common-utils' is not required.  Removing from installation order...
2026-10-10 06:58:59.146Z: Soft-dependency 'ghcr.io/devcontainers/features/git' is not required.  Removing from installation order...
2026-10-10 06:58:59.146Z: Soft-dependency 'ghcr.io/devcontainers/features/common-utils' is not required.  Removing from installation order...
2026-10-10 06:58:59.146Z: Soft-dependency 'ghcr.io/devcontainers/features/common-utils' is not required.  Removing from installation order...
2026-10-10 06:58:59.148Z: Soft-dependency 'ghcr.io/devcontainers/features/git' is not required.  Removing from installation order...
2026-10-10 06:58:59.148Z: Soft-dependency 'ghcr.io/devcontainers/features/common-utils' is not required.  Removing from installation order...
2026-10-10 06:58:59.349Z: Files to omit: ''
2026-10-10 06:58:59.490Z: Files to omit: ''
2026-10-10 06:58:59.650Z: Files to omit: ''
2026-10-10 06:58:59.789Z: Files to omit: ''
2026-10-10 06:59:00.005Z: Files to omit: ''
2026-10-10 06:59:00.019Z: $ubuntu --build-arg _DEV_CONTAINERS_IMAGE_USER=root --build-arg _DEV_CONTAINERS_FEATURE_CONTENT_SOURCE=dev_container_feature_content_temp --target dev_containers_target_stage -f /tmp/devcontainercli-root/container-features/0.83.3-1791615537011/Dockerfile.extended -t vsc-vision-infra-5ff015d1a0e8b58769115713acbbfb81116224666b5692dd621aac0777ff8a32-features /var/lib/docker/codespacemount/.persistedshare/empty-folder
2026-10-10 06:59:00.703Z: #0 building with "default" instance using docker driver

2026-10-10 06:59:00.704Z: #1 [internal] load .dockerignore
#1 transferring context: 2B 0.0s done
2026-10-10 06:59:00.712Z: #1 DONE 0.1s

#2 [internal] load build definition from Dockerfile.extended
#2 transferring dockerfile: 6.70kB done
#2 DONE 0.1s

2026-10-10 06:59:00.712Z: #3 [internal] load metadata for mcr.microsoft.com/devcontainers/base:ubuntu
#3 DONE 0.0s

#4 [context dev_containers_feature_content_source] load .dockerignore
#4 transferring dev_containers_feature_content_source: 2B done
#4 DONE 0.0s
2026-10-10 06:59:00.848Z: 
#5 [context dev_containers_feature_content_source] load from client
#5 transferring dev_containers_feature_content_source: 198.77kB done
2026-10-10 06:59:00.848Z: #5 DONE 0.1s

#6 [dev_containers_feature_content_normalize 1/3] FROM mcr.microsoft.com/devcontainers/base:ubuntu
#6 DONE 0.1s
2026-10-10 06:59:00.980Z: 
#7 [dev_containers_feature_content_normalize 2/3] COPY --from=dev_containers_feature_content_source devcontainer-features.builtin.env /tmp/build-features/
#7 DONE 0.1s

#8 [dev_containers_target_stage 2/9] RUN mkdir -p /tmp/dev-container-features
2026-10-10 06:59:02.306Z: #8 DONE 1.5s2026-10-10 06:59:02.306Z: 

#9 [dev_containers_feature_content_normalize 3/3] RUN chmod -R 0755 /tmp/build-features/
2026-10-10 06:59:02.434Z: #9 DONE 1.4s2026-10-10 06:59:02.435Z: 

#10 [dev_containers_target_stage 3/9] COPY --from=dev_containers_feature_content_normalize /tmp/build-features/ /tmp/dev-container-features
#10 DONE 0.1s
2026-10-10 06:59:02.592Z: 
2026-10-10 06:59:02.593Z: #11 [dev_containers_target_stage 4/9] RUN echo "_CONTAINER_USER_HOME=$( (command -v getent >/dev/null 2>&1 && getent passwd 'root' || grep -E '^root|^[^:]*:[^:]*:root:' /etc/passwd || ********) | cut -d: -f6)" >> /tmp/dev-container-features/devcontainer-features.builtin.env && echo "_REMOTE_USER_HOME=$( (command -v getent >/dev/null 2>&1 && getent passwd 'vscode' || grep -E '^vscode|^[^:]*:[^:]*:vscode:' /etc/passwd || ********) | cut -d: -f6)" >> /tmp/dev-container-features/devcontainer-features.builtin.env
2026-10-10 06:59:02.958Z: #11 DONE 0.5s
2026-10-10 06:59:03.115Z: 
2026-10-10 06:59:03.115Z: #12 [dev_containers_target_stage 5/9] RUN --mount=type=bind,from=dev_containers_feature_content_source,source=docker-in-docker_0,target=/tmp/build-features-src/docker-in-docker_0     cp -ar /tmp/build-features-src/docker-in-docker_0 /tmp/dev-container-features  && chmod -R 0755 /tmp/dev-container-features/docker-in-docker_0  && cd /tmp/dev-container-features/docker-in-docker_0  && chmod +x ./devcontainer-features-install.sh  && ./devcontainer-features-install.sh  && rm -rf /tmp/dev-container-features/docker-in-docker_0
2026-10-10 06:59:03.302Z: #12 0.337 ===========================================================================2026-10-10 06:59:03.302Z: 
#12 0.337 Feature       : Docker (Docker-in-Docker)
2026-10-10 06:59:03.451Z: #12 0.337 Description   : Create child containers *inside* a container, independent from the host's docker instance. Installs Docker extension in the container along with needed CLIs.
#12 0.337 Id            : ghcr.io/devcontainers/features/docker-in-docker2026-10-10 06:59:03.451Z: 
#12 0.337 Version       : 2.17.0
#12 0.337 Documentation : ********/devcontainers/features/tree/main/src/docker-in-docker
#12 0.337 Options       :
#12 0.337     VERSION="latest"
#12 0.337     MOBY="********"
#12 0.337     MOBYBUILDXVERSION="latest"
#12 0.337     DOCKERDASHCOMPOSEVERSION="v2"
#12 0.337     AZUREDNSAUTODETECTION="********"
#12 0.337     DOCKERDEFAULTADDRESSPOOL=""
#12 0.337     INSTALLDOCKERBUILDX="********"
#12 0.337     INSTALLDOCKERCOMPOSESWITCH="false"
#12 0.337     DISABLEIP6TABLES="false"
#12 0.337 ===========================================================================
2026-10-10 06:59:03.603Z: #12 0.640 (!) The 'moby' option is not supported on ubuntu 'resolute' because 'moby-cli' and related system packages are not available in that distribution.
#12 0.640 (!) To continue, either set the feature option '"moby": false' or use a different base image.
2026-10-10 06:59:03.727Z: #12 0.640 ERROR: Feature "Docker (Docker-in-Docker)" (ghcr.io/devcontainers/features/docker-in-docker) failed to install! Look at the documentation at ********/devcontainers/features/tree/main/src/docker-in-docker for help troubleshooting this error.
#12 ERROR: process "/bin/sh -c cp -ar /tmp/build-features-src/docker-in-docker_0 /tmp/dev-container-features  && chmod -R 0755 /tmp/dev-container-features/docker-in-docker_0  && cd /tmp/dev-container-features/docker-in-docker_0  && chmod +x ./devcontainer-features-install.sh  && ./devcontainer-features-install.sh  && rm -rf /tmp/dev-container-features/docker-in-docker_0" did not complete successfully: exit code: 1
------
 > [dev_containers_target_stage 5/9] RUN --mount=type=bind,from=dev_containers_feature_content_source,source=docker-in-docker_0,target=/tmp/build-features-src/docker-in-docker_0     cp -ar /tmp/build-features-src/docker-in-docker_0 /tmp/dev-container-features  && chmod -R 0755 /tmp/dev-container-features/docker-in-docker_0  && cd /tmp/dev-container-features/docker-in-docker_0  && chmod +x ./devcontainer-features-install.sh  && ./devcontainer-features-install.sh  && rm -rf /tmp/dev-container-features/docker-in-docker_0:
2026-10-10 06:59:03.728Z: 0.337     DOCKERDASHCOMPOSEVERSION="v2"
0.337     AZUREDNSAUTODETECTION="********"
0.337     DOCKERDEFAULTADDRESSPOOL=""
0.337     INSTALLDOCKERBUILDX="********"
0.337     INSTALLDOCKERCOMPOSESWITCH="false"
0.337     DISABLEIP6TABLES="false"
0.337 ===========================================================================
0.640 (!) The 'moby' option is not supported on ubuntu 'resolute' because 'moby-cli' and related system packages are not available in that distribution.
0.640 (!) To continue, either set the feature option '"moby": false' or use a different base image.
0.640 ERROR: Feature "Docker (Docker-in-Docker)" (ghcr.io/devcontainers/features/docker-in-docker) failed to install! Look at the documentation at ********/devcontainers/features/tree/main/src/docker-in-docker for help troubleshooting this error.
------
2026-10-10 06:59:03.730Z: Dockerfile.extended:24
--------------------
2026-10-10 06:59:03.730Z:   23 |     ENV DOCKER_BUILDKIT="1"
  24 | >>> RUN --mount=type=bind,from=dev_containers_feature_content_source,source=docker-in-docker_0,target=/tmp/build-features-src/docker-in-docker_0 \
  25 | >>>     cp -ar /tmp/build-features-src/docker-in-docker_0 /tmp/dev-container-features \
  26 | >>>  && chmod -R 0755 /tmp/dev-container-features/docker-in-docker_0 \
  27 | >>>  && cd /tmp/dev-container-features/docker-in-docker_0 \
  28 | >>>  && chmod +x ./devcontainer-features-install.sh \
  29 | >>>  && ./devcontainer-features-install.sh \
  30 | >>>  && rm -rf /tmp/dev-container-features/docker-in-docker_0
  31 |     
--------------------
ERROR: failed to build: failed to solve: process "/bin/sh -c cp -ar /tmp/build-features-src/docker-in-docker_0 /tmp/dev-container-features  && chmod -R 0755 /tmp/dev-container-features/docker-in-docker_0  && cd /tmp/dev-container-features/docker-in-docker_0  && chmod +x ./devcontainer-features-install.sh  && ./devcontainer-features-install.sh  && rm -rf /tmp/dev-container-features/docker-in-docker_0" did not complete successfully: exit code: 1
2026-10-10 06:59:03.742Z: Stop: Run: docker buildx build --load --build-arg BUILDKIT_INLINE_CACHE=1 --build-context dev_containers_feature_content_source=/tmp/devcontainercli-root/container-features/0.83.3-1791615537011 --build-arg _DEV_CONTAINERS_BASE_IMAGE=mcr.microsoft.com/devcontainers/base:ubuntu --build-arg _DEV_CONTAINERS_IMAGE_USER=root --build-arg _DEV_CONTAINERS_FEATURE_CONTENT_SOURCE=dev_container_feature_content_temp --target dev_containers_target_stage -f /tmp/devcontainercli-root/container-features/0.83.3-1791615537011/Dockerfile.extended -t vsc-vision-infra-5ff015d1a0e8b58769115713acbbfb81116224666b5692dd621aac0777ff8a32-features /var/lib/docker/codespacemount/.persistedshare/empty-folder
2026-10-10 06:59:03.742Z: {"outcome":"error","message":"Command failed: docker buildx build --load --build-arg BUILDKIT_INLINE_CACHE=1 --build-context dev_containers_feature_content_source=/tmp/devcontainercli-root/container-features/0.83.3-1791615537011 --build-arg _DEV_CONTAINERS_BASE_IMAGE=mcr.microsoft.com/devcontainers/base:ubuntu --build-arg _DEV_CONTAINERS_IMAGE_USER=root --build-arg _DEV_CONTAINERS_FEATURE_CONTENT_SOURCE=dev_container_feature_content_temp --target dev_containers_target_stage -f /tmp/devcontainercli-root/container-features/0.83.3-1791615537011/Dockerfile.extended -t vsc-vision-infra-5ff015d1a0e8b58769115713acbbfb81116224666b5692dd621aac0777ff8a32-features /var/lib/docker/codespacemount/.persistedshare/empty-folder","description":"An error occurred setting up the container."}
2026-10-10 06:59:03.742Z: Error: Command failed: docker buildx build --load --build-arg BUILDKIT_INLINE_CACHE=1 --build-context dev_containers_feature_content_source=/tmp/devcontainercli-root/container-features/0.83.3-1791615537011 --build-arg _DEV_CONTAINERS_BASE_IMAGE=mcr.microsoft.com/devcontainers/base:ubuntu --build-arg _DEV_CONTAINERS_IMAGE_USER=root --build-arg _DEV_CONTAINERS_FEATURE_CONTENT_SOURCE=dev_container_feature_content_temp --target dev_containers_target_stage -f /tmp/devcontainercli-root/container-features/0.83.3-1791615537011/Dockerfile.extended -t vsc-vision-infra-5ff015d1a0e8b58769115713acbbfb81116224666b5692dd621aac0777ff8a32-features /var/lib/docker/codespacemount/.persistedshare/empty-folder
2026-10-10 06:59:03.744Z:     at U9 (/.codespaces/agent/bin/node_modules/@devcontainers/cli/dist/spec-node/devContainersSpecCLI.js:467:1277)
2026-10-10 06:59:03.748Z:     at RL (/.codespaces/agent/bin/node_modules/@devcontainers/cli/dist/spec-node/devContainersSpecCLI.js:467:1021)
2026-10-10 06:59:03.748Z:     at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
2026-10-10 06:59:03.748Z:     at async AZ (/.codespaces/agent/bin/node_modules/@devcontainers/cli/dist/spec-node/devContainersSpecCLI.js:485:3870)
2026-10-10 06:59:03.748Z:     at async uC (/.codespaces/agent/bin/node_modules/@devcontainers/cli/dist/spec-node/devContainersSpecCLI.js:485:4989)
2026-10-10 06:59:03.748Z:     at async L5 (/.codespaces/agent/bin/node_modules/@devcontainers/cli/dist/spec-node/devContainersSpecCLI.js:666:205)
2026-10-10 06:59:03.748Z:     at async G5 (/.codespaces/agent/bin/node_modules/@devcontainers/cli/dist/spec-node/devContainersSpecCLI.js:665:15084)
2026-10-10 06:59:03.749Z:     at async /.codespaces/agent/bin/node_modules/@devcontainers/cli/dist/spec-node/devContainersSpecCLI.js:485:1188
2026-10-10 06:59:03.754Z: devcontainer process exited with exit code 1

====================================== ERROR ====================================
2026-10-10 06:59:03.764Z: Failed to create container.
=================================================================================
2026-10-10 06:59:03.764Z: Error: Command failed: docker buildx build --load --build-arg BUILDKIT_INLINE_CACHE=1 --build-context dev_containers_feature_content_source=/tmp/devcontainercli-root/container-features/0.83.3-1791615537011 --build-arg _DEV_CONTAINERS_BASE_IMAGE=mcr.microsoft.com/devcontainers/base:ubuntu --build-arg _DEV_CONTAINERS_IMAGE_USER=root --build-arg _DEV_CONTAINERS_FEATURE_CONTENT_SOURCE=dev_container_feature_content_temp --target dev_containers_target_stage -f /tmp/devcontainercli-root/container-features/0.83.3-1791615537011/Dockerfile.extended -t vsc-vision-infra-5ff015d1a0e8b58769115713acbbfb81116224666b5692dd621aac0777ff8a32-features /var/lib/docker/codespacemount/.persistedshare/empty-folder
2026-10-10 06:59:03.767Z: Error code: 1302 (UnifiedContainersErrorFatalCreatingContainer)

====================================== ERROR ====================================
2026-10-10 06:59:03.777Z: Container creation failed.
=================================================================================
2026-10-10 06:59:03.789Z: 

===================================== WARNING ===================================
2026-10-10 06:59:03.790Z: Creating recovery container.
=================================================================================

=================================================================================
2026-10-10 06:59:51.119Z: Creating container...
2026-10-10 06:59:51.157Z: $ devcontainer up --id-label Type=codespaces --workspace-folder /var/lib/docker/codespacemount/workspace/vision-infra --mount type=bind,source=/.codespaces/agent/mount/cache,target=/vscode --user-data-folder /var/lib/docker/codespacemount/.persistedshare --container-data-folder .vscode-remote/data/Machine --container-system-data-folder /var/vscode-remote --log-level trace --log-format json --update-remote-user-uid-default never --mount-workspace-git-root false --omit-config-remote-env-from-metadata --skip-non-blocking-commands --skip-post-create --config "/var/lib/docker/codespacemount/workspace/vision-infra/.devcontainer/devcontainer.json" --override-config /root/.codespaces/shared/merged_devcontainer.json --default-user-env-probe loginInteractiveShell --container-session-data-folder /workspaces/.codespaces/.persistedshare/devcontainers-cli/cache --secrets-file /root/.codespaces/shared/user-secrets-envs.json
2026-10-10 06:59:51.307Z: @devcontainers/cli 0.83.3. Node.js v18.20.8. linux 6.8.0-1064-azure x64.
2026-10-10 06:59:51.996Z: $alpine -c echo Container started
2026-10-10 06:59:52.021Z: Unable to find image 'mcr.microsoft.com/devcontainers/base:alpine' locally
2026-10-10 06:59:52.223Z: alpine: Pulling from devcontainers/base
2026-10-10 06:59:52.302Z: 
[1A[2Kd0c1d894c237: Pulling fs layer [1B
[1A[2K5b6175bd7c44: Pulling fs layer [1B
[1A[2K07d77b9465d1: Pulling fs layer [1B
[1A[2K09bd642602a2: Pulling fs layer [1B
[1A[2K4abf96649ed6: Pulling fs layer [1B
[1A[2Kfcb2d9375697: Pulling fs layer [1B
[1A[2K8da26f23d120: Pulling fs layer [1B[4A[2K09bd642602a2: Waiting [4B[3A[2K4abf96649ed6: Waiting [3B[2A[2Kfcb2d9375697: Waiting [2B[1A[2K8da26f23d120: Waiting [1B2026-10-10 06:59:52.390Z: [5A[2K07d77b9465d1: Downloading     135B/135B[5B[5A[2K07d77b9465d1: Verifying Checksum [5B[5A[2K07d77b9465d1: Download complete [5B2026-10-10 06:59:52.413Z: [7A[2K2026-10-10 06:59:52.413Z: d0c1d894c237: Downloading  48.35kB/3.849MB[7B2026-10-10 06:59:52.414Z: [6A[2K5b6175bd7c44: Downloading     409B/409B[6B2026-10-10 06:59:52.415Z: [6A[2K5b6175bd7c44: 2026-10-10 06:59:52.416Z: Verifying Checksum [6B[6A[2K5b6175bd7c44: Download complete [6B2026-10-10 06:59:52.442Z: [7A2026-10-10 06:59:52.442Z: [2K2026-10-10 06:59:52.442Z: d0c1d894c237: 2026-10-10 06:59:52.442Z: Verifying Checksum [7B[7A[2Kd0c1d894c237: Download complete [7B2026-10-10 06:59:52.462Z: [7A2026-10-10 06:59:52.462Z: [2Kd0c1d894c237: Extracting  65.54kB/3.849MB[7B2026-10-10 06:59:52.486Z: [4A[2K09bd642602a2: Downloading     223B/223B[4B2026-10-10 06:59:52.486Z: [4A[2K09bd642602a2: Verifying Checksum [4B[4A[2K09bd642602a2: Download complete [4B2026-10-10 06:59:52.505Z: [3A[2K4abf96649ed6: Downloading     237B/237B[3B[3A2026-10-10 06:59:52.505Z: [2K2026-10-10 06:59:52.505Z: 4abf96649ed6: Verifying Checksum [3B[3A[2K4abf96649ed6: Download complete [3B2026-10-10 06:59:52.538Z: [2A[2K2026-10-10 06:59:52.538Z: fcb2d9375697: Downloading  538.7kB/61.55MB[2B2026-10-10 06:59:52.565Z: [7A[2Kd0c1d894c237: Extracting  1.311MB/3.849MB[7B2026-10-10 06:59:52.640Z: [2A[2Kfcb2d9375697: Downloading  28.64MB/61.55MB[2B2026-10-10 06:59:52.669Z: [7A[2Kd0c1d894c237: Extracting  3.604MB/3.849MB[7B2026-10-10 06:59:52.676Z: [7A[2Kd0c1d894c237: Extracting  3.849MB/3.849MB[7B2026-10-10 06:59:52.754Z: [7A[2Kd0c1d894c237: Pull complete [7B[2A[2Kfcb2d9375697: Downloading  54.59MB/61.55MB[2B[1A[2K8da26f23d120: Downloading  538.7kB/218.3MB[1B2026-10-10 06:59:52.772Z: [2A[2Kfcb2d9375697: Verifying Checksum [2B[2A[2Kfcb2d9375697: Download complete [2B2026-10-10 06:59:52.774Z: [6A[2K5b6175bd7c44: Extracting     409B/409B[6B[6A[2K5b6175bd7c44: Extracting     409B/409B[6B2026-10-10 06:59:52.865Z: [1A[2K8da26f23d120: Downloading  22.15MB/218.3MB[1B2026-10-10 06:59:52.968Z: [1A[2K8da26f23d120: Downloading  39.99MB/218.3MB[1B2026-10-10 06:59:53.066Z: [1A[2K8da26f23d120: Downloading     60MB/218.3MB[1B2026-10-10 06:59:53.167Z: [1A[2K8da26f23d120: Downloading  78.92MB/218.3MB[1B2026-10-10 06:59:53.272Z: [1A2026-10-10 06:59:53.274Z: [2K8da26f23d120: Downloading  96.76MB/218.3MB[1B2026-10-10 06:59:53.370Z: [1A2026-10-10 06:59:53.372Z: [2K8da26f23d120: Downloading  120.6MB/218.3MB[1B2026-10-10 06:59:53.473Z: [1A2026-10-10 06:59:53.475Z: [2K8da26f23d120: Downloading  134.6MB/218.3MB[1B2026-10-10 06:59:53.572Z: [1A2026-10-10 06:59:53.572Z: [2K8da26f23d120: Downloading  152.5MB/218.3MB[1B2026-10-10 06:59:53.675Z: [1A[2K8da26f23d120: Downloading  171.9MB/218.3MB[1B2026-10-10 06:59:53.780Z: [1A[2K8da26f23d120: Downloading  188.1MB/218.3MB[1B2026-10-10 06:59:53.879Z: [1A[2K8da26f23d120: Downloading  207.6MB/218.3MB2026-10-10 06:59:53.880Z: [1B2026-10-10 06:59:53.929Z: [1A2026-10-10 06:59:53.929Z: [2K2026-10-10 06:59:53.929Z: 8da26f23d120: Verifying Checksum [1B[1A2026-10-10 06:59:53.930Z: [2K8da26f23d120: Download complete [1B2026-10-10 06:59:55.085Z: [6A[2K5b6175bd7c44: Pull complete [6B2026-10-10 06:59:55.091Z: [5A[2K07d77b9465d1: Extracting     135B/135B[5B2026-10-10 06:59:55.091Z: [5A[2K07d77b9465d1: Extracting     135B/135B[5B2026-10-10 06:59:58.177Z: [5A[2K07d77b9465d1: Pull complete 2026-10-10 06:59:58.177Z: [5B2026-10-10 06:59:58.183Z: [4A[2K09bd642602a2: Extracting     223B/223B[4B[4A[2K09bd642602a2: Extracting     223B/223B[4B2026-10-10 06:59:58.213Z: [4A[2K09bd642602a2: Pull complete [4B2026-10-10 06:59:58.218Z: [3A2026-10-10 06:59:58.218Z: [2K4abf96649ed6: Extracting     237B/237B[3B2026-10-10 06:59:58.220Z: [3A[2K4abf96649ed6: Extracting     237B/237B[3B2026-10-10 06:59:58.257Z: [3A[2K2026-10-10 06:59:58.258Z: 4abf96649ed6: Pull complete [3B2026-10-10 06:59:58.280Z: [2A[2Kfcb2d9375697: Extracting  557.1kB/61.55MB[2B2026-10-10 06:59:58.399Z: [2A[2Kfcb2d9375697: 2026-10-10 06:59:58.399Z: Extracting  2.785MB/61.55MB[2B2026-10-10 06:59:58.593Z: [2A[2K2026-10-10 06:59:58.593Z: fcb2d9375697: Extracting  6.685MB/61.55MB[2B2026-10-10 06:59:58.749Z: [2A[2Kfcb2d9375697: Extracting  7.242MB/61.55MB[2B2026-10-10 06:59:58.862Z: [2A[2Kfcb2d9375697: Extracting  10.03MB/61.55MB[2B2026-10-10 06:59:58.970Z: [2A[2K2026-10-10 06:59:58.971Z: fcb2d9375697: Extracting  13.93MB/61.55MB[2B2026-10-10 06:59:59.163Z: [2A[2Kfcb2d9375697: 2026-10-10 06:59:59.164Z: Extracting  14.48MB/61.55MB[2B2026-10-10 06:59:59.295Z: [2A2026-10-10 06:59:59.295Z: [2Kfcb2d9375697: Extracting  17.27MB/61.55MB[2B2026-10-10 06:59:59.421Z: [2A[2Kfcb2d9375697: Extracting  22.84MB/61.55MB[2B2026-10-10 06:59:59.520Z: [2A[2Kfcb2d9375697: Extracting  28.41MB/61.55MB[2B2026-10-10 06:59:59.628Z: [2A2026-10-10 06:59:59.630Z: [2Kfcb2d9375697: Extracting  33.42MB/61.55MB[2B2026-10-10 06:59:59.730Z: [2A[2Kfcb2d9375697: Extracting  38.99MB/61.55MB[2B2026-10-10 06:59:59.850Z: [2A2026-10-10 06:59:59.850Z: [2Kfcb2d9375697: Extracting  42.89MB/61.55MB[2B2026-10-10 06:59:59.953Z: [2A[2K2026-10-10 06:59:59.954Z: fcb2d9375697: Extracting  45.68MB/61.55MB[2B2026-10-10 07:00:00.222Z: [2A[2Kfcb2d9375697: Extracting  46.24MB/61.55MB[2B2026-10-10 07:00:00.383Z: [2A[2Kfcb2d9375697: Extracting  47.35MB/61.55MB[2B2026-10-10 07:00:00.598Z: [2A[2Kfcb2d9375697: Extracting  47.91MB/61.55MB[2B2026-10-10 07:00:00.764Z: [2A[2Kfcb2d9375697: Extracting  48.46MB/61.55MB[2B2026-10-10 07:00:00.901Z: [2A[2Kfcb2d9375697: Extracting  49.58MB/61.55MB[2B2026-10-10 07:00:01.009Z: [2A[2Kfcb2d9375697: Extracting  51.25MB/61.55MB[2B2026-10-10 07:00:01.254Z: [2A[2Kfcb2d9375697: Extracting  53.48MB/61.55MB2026-10-10 07:00:01.254Z: [2B2026-10-10 07:00:01.374Z: [2A[2K2026-10-10 07:00:01.374Z: fcb2d9375697: Extracting  56.26MB/61.55MB[2B2026-10-10 07:00:01.528Z: [2A[2K2026-10-10 07:00:01.528Z: fcb2d9375697: Extracting  57.38MB/61.55MB[2B2026-10-10 07:00:01.730Z: [2A[2Kfcb2d9375697: Extracting  57.93MB/61.55MB[2B2026-10-10 07:00:01.845Z: [2A[2Kfcb2d9375697: 2026-10-10 07:00:01.846Z: Extracting  58.49MB/61.55MB[2B2026-10-10 07:00:01.971Z: [2A[2Kfcb2d9375697: Extracting  59.05MB/61.55MB[2B2026-10-10 07:00:01.992Z: [2A[2Kfcb2d9375697: Extracting  61.55MB/61.55MB[2B2026-10-10 07:00:05.282Z: [2A[2Kfcb2d9375697: Pull complete [2B2026-10-10 07:00:05.319Z: [1A[2K8da26f23d120: Extracting  557.1kB/218.3MB[1B2026-10-10 07:00:05.427Z: [1A[2K8da26f23d120: Extracting  7.242MB/218.3MB[1B2026-10-10 07:00:05.530Z: [1A[2K8da26f23d120: Extracting  12.81MB/218.3MB[1B2026-10-10 07:00:05.635Z: [1A[2K8da26f23d120: Extracting  18.94MB/218.3MB[1B2026-10-10 07:00:05.742Z: [1A[2K8da26f23d120: Extracting  24.51MB/218.3MB[1B2026-10-10 07:00:05.845Z: [1A[2K8da26f23d120: Extracting  25.62MB/218.3MB[1B2026-10-10 07:00:06.021Z: [1A[2K8da26f23d120: Extracting  26.74MB/218.3MB[1B2026-10-10 07:00:06.176Z: [1A[2K8da26f23d120: Extracting  27.85MB/218.3MB[1B2026-10-10 07:00:06.284Z: [1A[2K8da26f23d120: Extracting  28.41MB/218.3MB[1B2026-10-10 07:00:06.387Z: [1A[2K8da26f23d120: Extracting  28.97MB/218.3MB2026-10-10 07:00:06.388Z: [1B2026-10-10 07:00:06.586Z: [1A[2K8da26f23d120: Extracting  30.08MB/218.3MB[1B2026-10-10 07:00:06.724Z: [1A[2K2026-10-10 07:00:06.725Z: 8da26f23d120: Extracting  33.42MB/218.3MB[1B2026-10-10 07:00:06.854Z: [1A[2K2026-10-10 07:00:06.854Z: 8da26f23d120: Extracting  34.54MB/218.3MB[1B2026-10-10 07:00:06.955Z: [1A2026-10-10 07:00:06.956Z: [2K8da26f23d120: Extracting  39.55MB/218.3MB[1B2026-10-10 07:00:07.063Z: [1A[2K8da26f23d120: Extracting  45.68MB/218.3MB[1B2026-10-10 07:00:07.169Z: [1A[2K8da26f23d120: Extracting  51.25MB/218.3MB[1B2026-10-10 07:00:07.275Z: [1A2026-10-10 07:00:07.276Z: [2K8da26f23d120: Extracting  56.26MB/218.3MB[1B2026-10-10 07:00:07.408Z: [1A[2K8da26f23d120: Extracting  60.16MB/218.3MB[1B2026-10-10 07:00:07.509Z: [1A[2K8da26f23d120: Extracting   63.5MB/218.3MB[1B2026-10-10 07:00:07.630Z: [1A2026-10-10 07:00:07.631Z: [2K8da26f23d120: Extracting  66.29MB/218.3MB[1B2026-10-10 07:00:07.736Z: [1A[2K8da26f23d120: Extracting   71.3MB/218.3MB[1B2026-10-10 07:00:07.841Z: [1A[2K2026-10-10 07:00:07.841Z: 8da26f23d120: Extracting  76.32MB/218.3MB[1B2026-10-10 07:00:07.962Z: [1A2026-10-10 07:00:07.963Z: [2K8da26f23d120: Extracting     83MB/218.3MB[1B2026-10-10 07:00:08.095Z: [1A[2K2026-10-10 07:00:08.095Z: 8da26f23d120: Extracting  85.79MB/218.3MB[1B2026-10-10 07:00:08.222Z: [1A[2K8da26f23d120: Extracting  88.57MB/218.3MB[1B2026-10-10 07:00:08.348Z: [1A2026-10-10 07:00:08.348Z: [2K8da26f23d120: Extracting  90.24MB/218.3MB[1B2026-10-10 07:00:08.492Z: [1A[2K8da26f23d120: Extracting  91.36MB/218.3MB[1B2026-10-10 07:00:08.617Z: [1A[2K8da26f23d120: Extracting  94.14MB/218.3MB[1B2026-10-10 07:00:08.713Z: [1A2026-10-10 07:00:08.714Z: [2K2026-10-10 07:00:08.714Z: 8da26f23d120: Extracting  98.04MB/218.3MB2026-10-10 07:00:08.714Z: [1B2026-10-10 07:00:08.815Z: [1A[2K8da26f23d120: Extracting  104.2MB/218.3MB[1B2026-10-10 07:00:08.917Z: [1A[2K8da26f23d120: Extracting  109.7MB/218.3MB[1B2026-10-10 07:00:09.023Z: [1A2026-10-10 07:00:09.023Z: [2K8da26f23d120: Extracting  117.5MB/218.3MB[1B2026-10-10 07:00:09.127Z: [1A[2K2026-10-10 07:00:09.127Z: 8da26f23d120: Extracting  123.1MB/218.3MB[1B2026-10-10 07:00:09.234Z: [1A[2K8da26f23d120: Extracting  128.7MB/218.3MB[1B2026-10-10 07:00:09.337Z: [1A[2K8da26f23d120: Extracting    132MB/218.3MB[1B2026-10-10 07:00:09.445Z: [1A[2K8da26f23d120: Extracting  135.9MB/218.3MB[1B2026-10-10 07:00:09.577Z: [1A[2K8da26f23d120: Extracting  138.7MB/218.3MB[1B2026-10-10 07:00:09.679Z: [1A[2K8da26f23d120: Extracting    142MB/218.3MB[1B2026-10-10 07:00:09.796Z: [1A[2K8da26f23d120: Extracting  144.8MB/218.3MB[1B2026-10-10 07:00:09.906Z: [1A[2K8da26f23d120: Extracting  148.2MB/218.3MB[1B2026-10-10 07:00:10.008Z: [1A[2K8da26f23d120: Extracting  151.5MB/218.3MB[1B2026-10-10 07:00:10.115Z: [1A[2K8da26f23d120: Extracting  158.2MB/218.3MB[1B2026-10-10 07:00:10.217Z: [1A[2K2026-10-10 07:00:10.218Z: 8da26f23d120: Extracting  164.9MB/218.3MB[1B2026-10-10 07:00:10.329Z: [1A[2K2026-10-10 07:00:10.330Z: 8da26f23d120: Extracting  171.6MB/218.3MB[1B2026-10-10 07:00:10.433Z: [1A2026-10-10 07:00:10.433Z: [2K8da26f23d120: Extracting  177.1MB/218.3MB[1B2026-10-10 07:00:10.538Z: [1A2026-10-10 07:00:10.539Z: [2K8da26f23d120: Extracting  183.8MB/218.3MB[1B2026-10-10 07:00:10.641Z: [1A2026-10-10 07:00:10.641Z: [2K8da26f23d120: Extracting  191.1MB/218.3MB[1B2026-10-10 07:00:10.744Z: [1A[2K2026-10-10 07:00:10.745Z: 8da26f23d120: Extracting  198.3MB/218.3MB[1B2026-10-10 07:00:10.851Z: [1A[2K2026-10-10 07:00:10.851Z: 8da26f23d120: Extracting  205.6MB/218.3MB[1B2026-10-10 07:00:10.959Z: [1A2026-10-10 07:00:10.960Z: [2K8da26f23d120: Extracting  209.5MB/218.3MB[1B2026-10-10 07:00:11.060Z: [1A[2K2026-10-10 07:00:11.061Z: 8da26f23d120: Extracting    210MB/218.3MB[1B2026-10-10 07:00:11.194Z: [1A[2K2026-10-10 07:00:11.194Z: 8da26f23d120: Extracting  211.7MB/218.3MB[1B2026-10-10 07:00:11.306Z: [1A[2K8da26f23d120: Extracting  212.8MB/218.3MB[1B2026-10-10 07:00:11.556Z: [1A[2K8da26f23d120: Extracting  214.5MB/218.3MB[1B2026-10-10 07:00:11.667Z: [1A[2K2026-10-10 07:00:11.668Z: 8da26f23d120: Extracting  215.6MB/218.3MB[1B2026-10-10 07:00:11.909Z: [1A2026-10-10 07:00:11.910Z: [2K8da26f23d120: Extracting  216.1MB/218.3MB[1B2026-10-10 07:00:12.053Z: [1A[2K8da26f23d120: Extracting  217.3MB/218.3MB[1B2026-10-10 07:00:12.204Z: [1A[2K8da26f23d120: Extracting  217.8MB/218.3MB[1B2026-10-10 07:00:12.695Z: [1A[2K8da26f23d120: Extracting  218.3MB/218.3MB[1B2026-10-10 07:00:22.846Z: [1A[2K2026-10-10 07:00:22.846Z: 8da26f23d120: 2026-10-10 07:00:22.846Z: Pull complete [1B2026-10-10 07:00:22.857Z: Digest: sha256:190bccaf23c9e88f21734f82b08b597310efcd4aa9240faf7e96d98c228753e3
2026-10-10 07:00:22.862Z: Status: Downloaded newer image for mcr.microsoft.com/devcontainers/base:alpine
2026-10-10 07:00:23.011Z: Container started
2026-10-10 07:00:23.233Z: Outcome: success User: vscode WorkspaceFolder: /workspaces/vision-infra
2026-10-10 07:00:23.240Z: devcontainer process exited with exit code 0

=================================================================================
2026-10-10 07:00:23.627Z: Running blocking commands...
2026-10-10 07:00:23.659Z: $ devcontainer up --id-label Type=codespaces --workspace-folder /var/lib/docker/codespacemount/workspace/vision-infra --mount type=bind,source=/.codespaces/agent/mount/cache,target=/vscode --user-data-folder /var/lib/docker/codespacemount/.persistedshare --container-data-folder .vscode-remote/data/Machine --container-system-data-folder /var/vscode-remote --log-level trace --log-format json --update-remote-user-uid-default never --mount-workspace-git-root false --omit-config-remote-env-from-metadata --skip-non-blocking-commands --expect-existing-container --config "/var/lib/docker/codespacemount/workspace/vision-infra/.devcontainer/devcontainer.json" --override-config /root/.codespaces/shared/merged_devcontainer.json --default-user-env-probe loginInteractiveShell --container-session-data-folder /workspaces/.codespaces/.persistedshare/devcontainers-cli/cache --secrets-file /root/.codespaces/shared/user-secrets-envs.json
2026-10-10 07:00:23.915Z: @devcontainers/cli 0.83.3. Node.js v18.20.8. linux 6.8.0-1064-azure x64.
2026-10-10 07:00:24.418Z: Outcome: success User: vscode WorkspaceFolder: /workspaces/vision-infra
2026-10-10 07:00:24.430Z: devcontainer process exited with exit code 0

=================================================================================
2026-10-10 07:00:24.441Z: Configuring codespace...

=================================================================================
2026-10-10 07:00:24.442Z: Finished configuring codespace.
