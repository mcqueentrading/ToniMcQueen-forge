# Tailscale Remote Access

ToniMcQueen Forge ships the official static Tailscale `mipsle` binaries as an
optional remote-access client. It does not enable or log into a tailnet during
installation.

The Creator 5 family stock kernel does not provide `/dev/net/tun`, so the
daemon always runs in userspace networking mode:

```sh
tailscaled --tun=userspace-networking
```

Persistent state is stored outside the replaceable payload:

```text
/usr/data/anvil-data/tailscale/
```

## Enable

SSH to the printer and run:

```sh
toniforge-tailscale-enable
```

Then log in to Tailscale:

```sh
toniforge-tailscale up --accept-dns=false --hostname=tonimcqueen-forge
```

For Headscale, keep the same printer client and point it at your Headscale
control server:

```sh
toniforge-tailscale up --login-server=https://HEADSCALE.example --accept-dns=false --hostname=tonimcqueen-forge
```

Do not put auth keys in the repository or the firmware package. Use an
interactive login or a short-lived key typed on the printer after installation.

## Check Status

```sh
toniforge-tailscale status
```

The daemon log is:

```text
/usr/data/logs/tailscale.log
```

## Disable

```sh
toniforge-tailscale-disable
```

This disables the service and runs `tailscale down`. The saved state remains in
`/usr/data/anvil-data/tailscale/` so it can be inspected or removed manually.

## Security Notes

Treat the printer as a root-access appliance. If it joins a tailnet, Moonraker,
SSH, Mainsail/Fluidd, and camera endpoints may become reachable from other
tailnet devices depending on ACLs. Use Tailscale ACLs, avoid exit-node routing
on the printer, and prefer MagicDNS/SSH access from trusted admin devices only.
