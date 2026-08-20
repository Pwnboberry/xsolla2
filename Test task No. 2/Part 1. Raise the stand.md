# Environment Setup

## Environment

- Operating System: Kali Linux
- Node.js: v20.20.2
- npm: 10.8.2

![](https://github.com/Pwnboberry/xsolla2/blob/main/screenshots/versions.png)

---

## Deployment Process

### Option 1 — Docker

The first deployment attempt used the official Docker image recommended by the project documentation.

```bash
docker run --rm -p 3000:3000 bkimminich/juice-shop:v17.1.1
```

The deployment could not be completed because Docker was unable to download the image from Docker Hub.

```text
Unable to find image 'bkimminich/juice-shop:v17.1.1' locally
docker: Error response from daemon:
Get "https://registry-1.docker.io/v2/":
dial tcp: lookup registry-1.docker.io:
i/o timeout
```

---

### Option 2 — Build from Source

The second attempt used the official GitHub repository.

```bash
git clone https://github.com/juice-shop/juice-shop.git
cd juice-shop
git checkout v17.1.1
npm install
```

During dependency installation, npm reported dependency resolution conflicts.

```text
npm ERR! code ERESOLVE
npm ERR! ERESOLVE could not resolve
...
```

Several attempts were made to resolve the issue, including testing different Node.js versions and using `--legacy-peer-deps`. However, the dependency conflicts could not be resolved in the local environment.

---

### Option 3 — Official Prebuilt Release

To continue the security assessment, the official prebuilt release package published by the OWASP Juice Shop project was used.

```bash
wget https://github.com/juice-shop/juice-shop/releases/download/v17.1.1/juice-shop-17.1.1_node20_linux_x64.tgz
```
![](https://github.com/Pwnboberry/xsolla2/blob/main/screenshots/clone%20of%20the%20repository.png)

```
tar -xzvf juice-shop-17.1.1_node20_linux_x64.tgz
cd juice-shop_17.1.1_node20_linux_x64
npm start
```
![](https://github.com/Pwnboberry/xsolla2/blob/main/screenshots/launching%20npm.png)

The application started successfully.

```text
info: Detected Node.js version v20.20.2 (OK)
info: Port 3000 is available (OK)
```

![](https://github.com/Pwnboberry/xsolla2/blob/main/screenshots/OWASP%20Juice%20Shop.png)

---

## Difficulties Encountered

Two deployment methods were attempted before the application was successfully launched.

The Docker-based deployment could not be completed because the Docker daemon was unable to download the image from Docker Hub due to network connectivity issues.

The second approach, building the application from source, resulted in dependency resolution conflicts during package installation. Several troubleshooting attempts were made, including switching Node.js versions and using alternative npm installation options, but the issue remained unresolved.

To proceed with the assignment, the official prebuilt release package provided by the OWASP Juice Shop project was used. This allowed the application to run successfully while preserving the same functionality required for the security assessment.

