# Развёртывание окружения

## Окружение

- Операционная система: Kali Linux
- Node.js: v20.20.2
- npm: 10.8.2

![](https://github.com/Pwnboberry/xsolla2/blob/main/screenshots/versions.JPG)

---

## Процесс развёртывания

### Вариант 1 — Docker

Первая попытка развёртывания была выполнена с использованием официального Docker-образа, рекомендованного в документации проекта.

```bash
docker run --rm -p 3000:3000 bkimminich/juice-shop:v17.1.1
```

Развёртывание не удалось, так как Docker не смог загрузить образ из Docker Hub.

```text
Unable to find image 'bkimminich/juice-shop:v17.1.1' locally
docker: Error response from daemon:
Get "https://registry-1.docker.io/v2/":
dial tcp: lookup registry-1.docker.io:
i/o timeout
```

---

### Вариант 2 — Сборка из исходного кода

Вторая попытка была выполнена с использованием официального репозитория GitHub.

```bash
git clone https://github.com/juice-shop/juice-shop.git
cd juice-shop
git checkout v17.1.1
npm install
```

Во время установки зависимостей npm сообщил о конфликте зависимостей.

```text
npm ERR! code ERESOLVE
npm ERR! ERESOLVE could not resolve
...
```

Для решения проблемы было предпринято несколько попыток, включая использование разных версий Node.js и установку зависимостей с параметром `--legacy-peer-deps`. Однако устранить конфликт зависимостей в локальном окружении не удалось.

---

### Вариант 3 — Готовая официальная сборка

Чтобы продолжить выполнение задания, была использована официальная готовая сборка (prebuilt release), опубликованная разработчиками OWASP Juice Shop.

```bash
wget https://github.com/juice-shop/juice-shop/releases/download/v17.1.1/juice-shop-17.1.1_node20_linux_x64.tgz
```

![](https://github.com/Pwnboberry/xsolla2/blob/main/screenshots/clone%20of%20the%20repository.JPG)

```bash
tar -xzvf juice-shop-17.1.1_node20_linux_x64.tgz
cd juice-shop_17.1.1_node20_linux_x64
npm start
```

![](https://github.com/Pwnboberry/xsolla2/blob/main/screenshots/launching%20npm.JPG)

После этого приложение успешно запустилось.

```text
info: Detected Node.js version v20.20.2 (OK)
info: Port 3000 is available (OK)
```

![](https://github.com/Pwnboberry/xsolla2/blob/main/screenshots/OWASP%20Juice%20Shop.JPG)

---

## Возникшие сложности

Перед успешным запуском приложения были предприняты две попытки развёртывания.

Первый вариант с использованием Docker не удалось реализовать, поскольку Docker не смог загрузить образ из Docker Hub из-за проблем с сетевым подключением.

Вторая попытка, предусматривавшая сборку приложения из исходного кода, завершилась конфликтом зависимостей при установке пакетов. Для решения проблемы были предприняты несколько попыток, включая смену версии Node.js и использование альтернативных параметров установки npm, однако устранить конфликт не удалось.

Чтобы продолжить выполнение задания, была использована официальная готовая сборка OWASP Juice Shop. Это позволило успешно запустить приложение, сохранив весь необходимый функционал для проведения анализа безопасности.
