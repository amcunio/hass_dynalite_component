---
title: "Philips Dynalite"
description: "Instructions on setting up Philips Dynalite within Home Assistant."
---

Philips Dynalite support is integrated into Home Assistant as a hub that can drive the light platforms. 

There is currently support for the following device types within Home Assistant:

- Lights
- Switches
- Covers

A Philips Dynalite hub connects to the Dynet network, which is composed of areas, channels, and preset. 

A Dynalite area typically (although not necessarily) defines some physical area, such as a room. 

Each area can have one or more channels that correspond to the different devices they control. A channel can relate to a dimmable light, or other devices.

Additionally, each area can have one or more presets that determine the behavior of all the channels, and sometimes trigger additional actions. Typically, preset 1 in an area means 'on', and preset '4' means off. Additional presets could be used for scenes and dimming.

## Configuration

Since Philips Dynalite has virtually no auto-discover capabilities, it needs to be configured via the `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
dynalite:
  bridges:
    - host: DEVICE_IP_ADDRESS
```

{% configuration %}
host:
  description: The IP address of the bridge (e.g., 192.168.1.10).
  required: true
  type: string
port:
  description: Port number of the bridge.
  required: false
  type: integer
  default: 12345
name:
  description: Name for the bridge.
  required: false
  type: string
  default: dynalite
active:
  description: Actively query network. When starting, it will query all devices for their current status, and also will send queries when some changes are in progress (e.g. lights dimming or covers moving). Better experience but creates more load on the Dynalite network. Value can be 'on', 'off', our 'init', where 'init' will only send queries during the initial init of Home Assistant
  required: false
  type: [boolean, string]
  default: false
polltimer:
  description: Polling interval for devices in transition. Value in seconds. When devices are in transition (e.g., a light fading), it will ask for a new state every X seconds until it is at the target level. Only relevant when active is set to 'on'.
  required: false
  type: float
  default: 1.0
autodiscover:
  description: Enable auto-discover. As Dynalite does not support native autodiscovery, this tracks events on your network, so if you turn on a light, it will be added to Home Assistant.
  required: false
  type: boolean
  default: false
default:
  description: Global defaults for the system
  required: false
  type: map
  keys:
    fade:
      description: Default fade
      required: false
      type: float
area:
  description: Definition for the various Dynalite areas.
  required: true
  type: map
  keys:
    AREA_NUMBER:
      description: The Dynalite area number, 1-255.
      required: true
      type: map
      keys:
        name:
          description: Name of the area.
          required: true
          type: string
        template:
          description: "Type of template to use for the area. Supported values are: 'room', 'trigger', and 'timecover'. They are described in details below in the **template** section. If the template parameters are different than defaults, they can be overriden in this section as well"
          require: false
          type: string
          default: No template
        TEMPLATE_PARAMS:
          description: "This can be any of the settings of the template. For example, for template 'room': 'room_on' and 'room_off' are possible options"
          required: false
          type: [integer, float]
          default: Value from **template** section or system defaults
        fade:
          description: Fade time for the area, in seconds.
          required: false
          type: float
          default: 2.0
        preset:
          description: Specific presets for the area.
          required: false
          type: map
          keys:
            PRESET_NUMBER:
              description: The Dynalite preset number in the area.
              required: true
              type: map
              keys:
                name:
                  description: Name of the preset.
                  required: false
                  type: string
                  default: AREA_NAME Preset PRESET_NUMBER
                fade:
                  description: Fade time for the preset, in seconds.
                  required: false
                  type: float
                  default: 2.0
        nodefault:
          description: Do not use the default presets defined globally, but only the specific ones defined for this area.
          required: false
          type: boolean
          default: false
        channel:
          description: Map of the channels in this area.
          required: false
          type: map
          keys:
            CHANNEL_NUMBER:
              description: The Dynalite channel number in the area, 1-255.
              required: true
              type: map
              keys:
                name:
                  description: Name of the channel.
                  required: false
                  type: string
                  default: AREA_NAME Channel CHANNEL_NUMBER
                type:
                  description: Type of entity this should appear as. Can be either 'light' or if this is a device that is not a light (e.g. water heater), can be 'switch'
                  require: false
                  type: string
                  default: light
                fade:
                  description: Fade time for the channel, in seconds.
                  required: false
                  type: float
                  default: 2.0
preset:
  description: Default presets for any area without the **nodefault** option
  required: false
  type: map
  keys:
    PRESET_NUMBER:
      description: The Dynalite preset number in the area.
      required: true
      type: map
      keys:
        name:
          description: Name of the preset. When used in an area, it will be 'AREA_NAME name'. For example, if a room's name is "Kitchen" and preset 4 is defined with name "Off", it will appear in HA as **Kitchen Off**          
          required: false
          type: string
          default: AREA_NAME Preset PRESET_NUMBER
        fade:
          description: Fade time for the preset, in seconds.
          required: false
          type: float
          default: 2.0
template:
  description: Set the default parameters for the templates.
  required: false
  type: map
  keys:
    room:
      description: This is used to define a room that has a preset to turn on all the channels in the area and a preset to turn off.
      required: false
      type: map
      keys:
        room_on:
          description: Preset to turn area on.
          required: false
          type: integer
          default: 1
        room_off:
          description: Preset to turn area off.
          required: false
          type: integer
          default: 4
    trigger:
      description: This is used to define a preset that acts as a trigger, such as a door buzzer. It only supports turning on.
      required: false
      type: map
      keys:
        trigger:
          description: Preset to trigger the action.
          required: false
          type: integer
          default: 1
    timecover:
      description: "This is used to define a cover that has 3 presets: open, close, and stop. Potentially can also use a channel that some systems (e.g. Control4) use to also send commands to open and close the cover. It uses the duration it takes to open or close to determine position. In addition, many times, these covers include tilt by opening or closing for a short time, so this can be defined as well."
      required: false
      type: map
      keys:
        open:
          description: Preset to open the cover.
          required: false
          type: integer
          default: 1
        close:
          description: Preset to close the cover.
          required: false
          type: integer
          default: 2
        stop:
          description: Preset to stop the cover.
          required: false
          type: integer
          default: 4
        channelcover:
          description: Channel that monitors the cover.
          required: false
          type: integer
          default: 1
        duration:
          description: Time in seconds it takes to open or close the cover.
          required: false
          type: integer
          default: 60
        tilt:
          description: Time in seconds it takes to open or close the cover tilt. '0' means that the cover does not support tilt.
          require: false
          type: integer
          default: 0
        class:
          description: Type of cover for Home Assistant. The supported cover classes are currently 'awning', 'blind', 'curtain', 'damper', 'door', 'garage', 'shade', 'shutter', and 'window'.
          require: false
          type: string
          default: shutter
{% endconfiguration %}

## Examples

```yaml
# Example configuration.yaml entry specifying optional parameters
dynalite:
  bridges:
    - host: DEVICE_IP_ADDRESS
      port: 12345
      autodiscover: true
      polltimer: 1
      area:
        '1':
          name: Office
          template: room
        '2':
          name: Living Room
          template: room
          nodefault: true
          room_on: 2
          room_off: 5
          channel:
            '2': 
              name: Entrance Spot
              fade: 10.0
            '3': 
              name: Dining Table
        '4':
          name: Curtain
          template: timecover
      preset:
        '1':
          name: 'On'
        '4':
          name: 'Off'
      template:
        room:
          room_on: 1
          room_off: 4
```

## Initial configuration and discovery

Maybe the most difficult thing about a Dynalite system is finding out the areas and channel mapping. If you have them or have access to the Dynalite software and your configuration files, this could be easy,
but in the likely case that your system was installed by an integrator, you will have to discover them on your own.

This is where the `autodiscover` option comes handy. If it is on, the component will track the Dynet network and every time a device is used, it will be added to Home Assistant. It will initially show as "Area 123 Channel 7", but you can then add it to your `configuration.yaml` with the correct configuration.

For example, you would go to your kitchen light and turn it on. Now you log into Home Assistant and see what the channel was. If there was more than one discovered (e.g., someone turned off the living room lights), you can try one, turn it on and off in Home Assistant and see which light it affects.

The initial process can be a bit time consuming and tedious, but it only has to be done once. Once you are done configuring, it is better to set `autodiscover` to `false`, since there are many "fake" channels and areas that the system uses for internal communication and you do not want to have visible.
