# klipper-repl

_The missing Klipper command line._

![Screenshot of klipper-repl](assets/screenshot.png)

`klipper-repl` is a command line reimplementation of the browser-based G-Code
console implemented by Klipper frontends like [Fluidd](https://docs.fluidd.xyz/)
and [Mainsail](https://docs.mainsail.xyz/). Its features include:
- Automatic reconnection if Klipper restarts or is unavailable
- Scripting support
- Multiple G-Code commands per line -- use `,` as a separator
- Syntax highlighting for both G-Code and user-defined macros
- Tab autocompletion for user-defined macros
- M112 emergency stop processing
- Support for multiple printers via [GNU
  Parallel](https://www.gnu.org/software/parallel/)

## Installing
### Via a Nix flake
If you have the [Nix package manager](https://nixos.org/), this package is
available as a [Nix flake](https://nixos.wiki/wiki/Flakes). An example
`flake.nix` for a host running Klipper is:

``` nix
{
  inputs = {
    nix-doom-emacs.url = "github:unjordy/klipper-repl";
  };

  outputs = {
    self,
    nixpkgs,
    klipper-repl,
    ...
  }: {
    nixosConfigurations.klipperHost = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        {
          environment.systemPackages = [
            klipper-repl.packages.${system}.default
          ];
        }
      ];
    };
  };
}
```

You can also run `klipper-repl` without installing it using

``` nix
nix run github:unjordy/klipper-repl
```

### Via pip

``` sh
pip install klipper-repl
```

## Usage
### Running interactively
Assuming `klipper-repl` is running on the same host you're currently logged
into, and that your [Klipper API](https://www.klipper3d.org/API_Server.html)
socker is located at `/run/klipper/api`, you can get an interactive G-Code REPL
with:

``` sh
klipper-repl /run/klipper/api
```

### Usage in scripts
You can evaluate one line of G-Code as follows. Note that you can use the `,`
character to incorporate multiple G-Code commands into one line, and that G-Code
is case-insensitive (but generally gets converted to uppercase by Klipper).

``` sh
klipper-repl /run/klipper/api g28, screws_tilt_calculate
```

### Emergency stop
Typing the command `m112` into `klipper-repl` will immediately discard the rest
of the command buffer and send an emergency stop signal to Klipper.

### Running remotely
`klipper-repl` doesn't provide any of its own facilities for operating on remote
systems. Instead, install `klipper-repl` on each of your Klipper hosts and use
`ssh` to run it remotely. For example, to get a remote interactive REPL:

``` sh
ssh klipper@klipper-host -t klipper-repl /run/klipper/api
```

Note that the `-t` argument to `ssh` allocates a TTY for `klipper-repl`, which
it needs to properly render its prompt.

For convenience, it's recommended to create a shell function or script that runs
`klipper-repl` for a specific Klipper host and socket. For example:

``` sh
#!/usr/bin/env bash

ssh klipper@klipper-host -t klipper-repl /run/klipper/api $@
```

Save this as something like `klipper-host-repl` and mark it executable, and you
can use it exactly like you would `klipper-repl`.

### Sending commands to multiple printers
You can combine `klipper-repl` with [GNU
Parallel](https://www.gnu.org/software/parallel/) to run G-Code commands across
multiple printers and multiple Klipper hosts. GNU Parallel is an incredibly
flexible way to run multiple commands simultaneously and I highly recommend
reading its manual, but an example of using it with `klipper-repl` to control
multiple printers is:

``` sh
parallel klipper-repl /run/klipper/api-{} ::: printer1 printer2
```
