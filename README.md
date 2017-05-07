# ocidiet -  Container Image Minimizer

Experimntal container image minimizer. Uses `ldd` and can possibly use
`strace` to detect the files needed by a binary and thus it minimizes
the image size. It copies only files needed into a tar which than can
be `ADD`ed to for example `busybox:uclibc` image.


## Prerequisites

- Python 2.7 or Python 3+
- ldd - [ldd(1)](https://linux.die.net/man/1/ldd)


## USAGE

## Example on how to build small node.js app

using the offical node 6 image

```
$ docker run -ti -v $(pwd):/usr/src/app node:6 bash
```

Inside the node:6 container install your app

```
> cd /usr/src/app
> npm install
> ./ocidiet.py -t myapp.tar -b `which node` -e /etc/nsswitch.conf \
  /etc/resolv.conf myapp/node_modules myapp/package.json myapp/index.js
> exit
```

and finally on the host build you final app image

```
# docker build -t myapp .
```
using the following `Dockerfile`:

```Dockerfile

FROM busybox:uclibc

ADD myapp.tar /

ENTRYPOINT ["/usr/local/bin/node"]
CMD ["/usr/src/app/myapp/index.js"]

```

Now you have a node image which has roughly 37 MB + size of your app.

