# UAV Firmware

This repository documents my autonomous quadcopter project, including manual flight testing, flight-controller setup, waypoint navigation experiments, and future RF/RSSI-based signal analysis.

## Project Status

Current stage: manual flight testing and system verification.

Completed:

* Frame assembly
* Motor and ESC calibration
* Flight-controller calibration
* Controller setup

Next steps:

* Inspect hardware after transport
* Verify flight modes and failsafe settings
* Perform safe manual hover test
* Test GPS hold / loiter mode
* Begin simple waypoint-based autonomous missions
* Document flight logs and debugging notes

## Project Goals

The goal of this project is to build hands-on experience with UAV systems, embedded control, flight testing, autonomous navigation, and RF-related sensing concepts.

Long-term goals include:

* Manual flight control testing
* Return-to-home verification
* Waypoint mission planning
* Flight log analysis
* RF signal strength data collection
* Basic signal-location estimation using RSSI measurements

## Repository Structure

```text
UAV-firmware/
├── README.md
├── docs/
│   ├── safety-checklist.md
│   ├── manual-flight-test-plan.md
│   ├── autonomy-plan.md
│   └── flight-log-template.md
├── firmware/
│   └── src/
├── missions/
│   └── waypoint-tests/
├── logs/
│   └── sanitized-flight-logs/
├── media/
│   └── images-videos/
└── notes/
    ├── rf-notes.md
    └── networking-notes.md
```

## Safety Note

Flight testing will be done step by step, starting with manual control and basic hover testing before moving into autonomous missions. Public documentation will avoid sharing private locations, sensitive flight data, or unsafe testing details.
