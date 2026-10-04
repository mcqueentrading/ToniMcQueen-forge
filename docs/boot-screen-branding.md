# Boot Screen Branding

Reforge draws its early boot screen directly to `/dev/fb0` before HelixScreen
starts. The title text is configurable without editing Python.

The packaged default is:

```text
/usr/data/anvil/config/boot-screen.conf
```

The persistent printer-local override is:

```text
/usr/data/anvil-data/config/boot-screen.conf
```

Use this format:

```text
BOOT_TITLE=ToniMcQueen's Forge
```

Keep the title short. The renderer uses a tiny built-in uppercase font so the
boot screen can work with no GUI toolkit, image decoder, or font files.

Preview locally from the fork:

```sh
./bin/preview-boot-screen.py --title "ToniMcQueen's Forge"
```

Rendered PNGs are written to:

```text
work/boot-screen/
```
