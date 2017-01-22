Python control for Qube LED bulbs
=================================

A simple Python API for controlling LED bulbs from [Qube](http://www.qube-smarthome.com). This only covers local control via Bluetooth - the protocol for remote control should be similar, but is not yet implemented.

Example use
-----------

This will connect and set the bulb to full red, no green, no blue and half white using 05325983 as the firmware setup key (see below)
```
import qube

bulb = qube.qube("0A:84:20:16:00:01", "05325983")
bulb.connect()
bulb.set_rgbw(0xff, 0x00, 0x00, 0x80)
```

This will turn the bulb on
```
bulb.on()
```

This will turn the bulb off
```
bulb.off()
```

Get a list of the current red, green and blue values
```
(red, green, blue) = bulb.get_colour()
```

Get the current white intensity
```
white = bulb.get_state()
```

Get a boolean describing whether the bulb is on or off
```
on = bulb.get_on()
```

Obtaining the firmware setup key
================================

If your device has been associated with your Qube account, it will require an authentication key for communication. This can be obtained as following. First, obtain an authentication token for your account:

```
curl -X POST https://home.qube-smarthome.com/api/v1/auth/tokens --data-urlencode email=your_email --data-urlencode password=your_password --data-urlencode grantType=password
```

where your_email and your_password are the email address and password used for your account. This will return some output including a field marked "accessToken". Now run:

```
curl 'https://home.qube-smarthome.com/api/v1/users/?expand=mobiles,houses,rooms,appliances,status&mobileFields=osTypeID,identifier,mobileClientUUID' -H "Authorization: Bearer your_token"
```

where your_token is the access token from the previous step. This will return a JSON block containing information about all associated devices in your account. Find the applianceFirmwareSetupKey field for the appropriate device and use that in the setup call.
