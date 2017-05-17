# ocidiet -  Container Image Minimizer

Experimntal container image minimizer. Uses `ldd` and can possibly use
`strace` in the future to detect the files needed by a binary. It minimizes
the image size because it copies only files needed into a tar which than can
be `ADD`ed to for example `busybox:uclibc` image or from scratch.

## Prerequisites

- Python 2.7 or Python 3+
- ldd - [ldd(1)](https://linux.die.net/man/1/ldd)


## What can be done with it?

There are two main use cases.

- building smaller images from other base images
- building images from local environment


## Build small node.js app from offical node image

Using the offical node 6 image

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

## Create image from local environment

Another option usefull for quick shipping and sharing is to use it for
creating images based on local dev environment. Usefull for compiled
C/C++ projects.

Taking the hello world example

```c
#include <stdio.h>

int main(void) {
    printf("Hello World\n");
    return 0;
}
```

and compiling it with `gcc hello.c -o hello` we now have an app which
needs at least libc. If we install it to let's say `/usr/local/bin` we
can create a container image by first creating the tar 

```sh
$ ./ocidiet.py -t hello.tar -b /usr/local/bin/hello
```
and then using the following Dockerfile

```Dockerfile

FROM busybox:uclibc

ADD hello.tar /

ENTRYPOINT ["/usr/local/bin/hello"]

```
building the final image.

```sh
$ docker build -t hello .
```
which contains really just the `busybox:uclibc` files and the `hello`
binary and correct version of `libc`.

If you don't need the busybox to poke around the running container
just build it from scratch.

```Dockerfile

FROM scratch

ADD hello.tar /

ENTRYPOINT ["/usr/local/bin/hello"]

```
and save around 1.2 MB.
