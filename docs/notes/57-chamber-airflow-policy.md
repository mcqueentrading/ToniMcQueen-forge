# Creator 5 Pro chamber airflow policy

Date: 2026-10-04

## Hardware model

The Creator 5 Pro aux/chamber airflow is not one simple fan.

- `chamber_loop_fan` recirculates chamber air.
- `chamber_cool_fan` pulls cooler outside air into the chamber.
- `chamber_fan` exhausts/filters chamber air.
- `chamber_heat_fan` cools the chamber heater assembly and follows
  `chamber_heater` as a Klipper `[heater_fan]`.

Stock behaviour couples airflow that should be independent. That is acceptable
for PLA cooling, but it fights warm-chamber materials: ABS, ASA, nylon and
similar materials need stable warm air, while the outside-air fan and exhaust
pull heat out of the enclosure.

## Sensors

The fork has chamber temperature, not outside ambient temperature.

- Creator 5 Pro declares `heater_generic chamber_heater` on PC1. That PC1
  thermistor is chamber air feedback for the heater.
- Plain Creator 5 declares `temperature_sensor chamber` on the same PC1 pin.
- `temperature_sensor ptcTemp` on PC0 is the heater/element-side sensor.
- There is no declared outside-room/inlet-air ambient sensor.

So the firmware can control policy from chamber target and chamber actual
temperature, but it cannot directly know whether incoming outside air is 8 C or
25 C without added hardware.

## Fork policy

`ff-chamber.cfg` owns the FlashForge-style `M106` P-map.

- `M106` or `M106 P1` controls the model fan, `fanM106`.
- `M106 P2` controls recirculation and outside-air cooling.
- `M106 P3` controls chamber exhaust/filtering.
- `M106 P101` is accepted but ignored unless a future package declares that
  hardware.

When `chamber_heater` has a target above zero:

- `M106 P2` keeps `chamber_loop_fan` active but suppresses
  `chamber_cool_fan`.
- `M106 P3` suppresses `chamber_fan`.

This prevents generic aux-cooling commands from fighting the chamber heater.

PLA remains simple: if the chamber heater target is zero, `M106 P2` and
`M106 P3` behave as cooling/exhaust commands.

Do not treat Klipper's chamber `max_temp` as a normal operating target.
OpenCreator community notes warn that chamber-area plastic can deform above
about 70 C. Keep normal ABS/ASA/nylon chamber targets below that unless the
specific printer hardware has been inspected and proven safe.

## Overrides

Warm-material prints may still need a short cold-air or exhaust blast for a
bridge or overhang. The fork allows explicit overrides:

```gcode
M106 P2 S180 COLD=1
M106 P3 S180 EXHAUST=1
```

Global policy can be changed at runtime:

```gcode
FF_CHAMBER_AIR_POLICY COLD_AIR_WHILE_HEATING=0 EXHAUST_WHILE_HEATING=0 LOOP=0.3
```

Defaults are conservative for ABS/ASA/nylon:

- cold outside air while heating: off
- exhaust while heating: off
- recirculation while heating: 30 %

## Calibration direction

Calibrate by measuring chamber response, not outside ambient:

1. Record chamber actual temperature with bed heat only.
2. Record chamber actual temperature with `M141`/`M191` chamber heat.
3. Compare recovery time after `M106 P2` with and without `COLD=1`.
4. Compare exhaust recovery after `M106 P3` with and without `EXHAUST=1`.
5. Set material profiles so PLA leaves chamber target at zero, while ABS/ASA
   and nylon use chamber targets and the guarded airflow policy.

If later hardware adds an inlet/outside thermistor, the policy can be upgraded
from target-based gating to real delta control.
