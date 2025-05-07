# TP File Transfer

## Dev config on VSCode

**Install Flake8 (linter) and autopep 8 (formatter that follows PEP8 standard).** 
    Then, settings file should override format on save and added code should be compliant. 
    NOTE: Seems like formatter doesn't handle "too long" lines so the line jump should be added manually


Local:

python3 start-server.py -v -H 127.0.0.1 -p 1234 -s ./files/server -r sw

python3 upload.py -v -H 127.0.0.1 -p 1234 -s ./files/client/clientfile.txt -n uploadfile.txt -r sw

python3 download.py -v -H 127.0.0.1 -p 1234 -d ./files/client/downloadfile.txt -n serverfile.txt -r sw


Mininet:

sudo -E mn --topo single,3

Agrega pkt loss
h1 tc qdisc add dev h1-eth0 root netem loss 5%
h2 tc qdisc add dev h2-eth0 root netem loss 5%

python3 start-server.py -v -H 10.0.0.1 -p 1234 -s ./files/server -r sw

h2 python3 upload.py -v -H 10.0.0.1 -p 1234 -s ./files/client/clientfile.txt -n uploadfile.txt -r sw

h2 python3 download.py -v -H 10.0.0.1 -p 1234 -d ./files/client/downloadfile.txt -n serverfile.txt -r sw
