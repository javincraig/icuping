# icuping
Python Script that runs a constant ping against a list of hosts and the default gateway from each interface with a gateway.

icuping is pronounced I.C.U.Ping

This was created because of a specific use case where monitoring the network from multiple interfaces on a device was a requirement.  In this specific case we wanted to monitor both the wireless connection and wired connection so we could easliy corrolate outages in a VERY rudimentry way. When a connection is lost it also reports the mac address of the default gateway (an attempt at detecting ARP poisoning). It lists the time that the connection went down and what time it came back up. 

