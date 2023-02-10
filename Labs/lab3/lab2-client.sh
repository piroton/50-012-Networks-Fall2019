#!/bin/zsh

echo "Welcome to the Lab 2 Client!"

site="127.0.0.1:5000"
dice="127.0.0.1:5000/dice"
memory="127.0.0.1:5000/memory"
rolls="127.0.0.1:5000/rolls"

echo "Testing GET function for root directory:" 
echo "curl $site -X GET"
curl $site -X GET

text1="ROLL 1D6 10 FIREBALL"
text2="ROLL 1D6+1D8 1 STRIKE"
text3="ROLL 3D6 1 ICICLE"
text4="ROLL 1D6+5D8 1 BIG BOMB"
text5="ROLL 3D6+3D8 1 NICE MEME"

echo "Testing POST function for dice rolling with text/plain"
echo "The format for the plain text data is of the form: [ROLL] [numdice]d[dice sides] [modifier:int] [name]"
echo "curl $dice -X POST --header 'Content-Type: text/plain' --data $text1"
curl $dice -X POST --header 'Content-Type: text/plain' --data "$text1"
echo ""
sleep 1s
echo "curl $dice -X POST --header 'Content-Type: text/plain' --data $text2"
curl $dice -X POST --header 'Content-Type: text/plain' --data "$text2"
echo ""
echo "curl $dice -X POST --header 'Content-Type: text/plain' --data $text3"
curl $dice -X POST --header 'Content-Type: text/plain' --data "$text3"
echo ""
echo "curl $dice -X POST --header 'Content-Type: text/plain' --data $text4"
curl $dice -X POST --header 'Content-Type: text/plain' --data "$text4"
echo ""
echo "curl $dice -X POST --header 'Content-Type: text/plain' --data $text5"
curl $dice -X POST --header 'Content-Type: text/plain' --data "$text5"
echo ""
sleep 4s
json1='{"name": "fireball", "d6":8, "mod":5}'
json2='{"name": "magic missile", "d4":10, "mod":100}'
json3='{"name": "pew pew", "d25":1, "mod":-1}'

echo "Testing POST function for dice rolling with JSON:"
echo 'The format of the POST JSON is the following: {"name": [name], "D[x]": [number of D[x] to roll], "mod": [modifier number to add to total],}'
echo "curl $dice -X POST --header 'Content-Type: application/json' --data $json1"
curl $dice -X POST --header 'Content-Type: application/json' --data $json1
echo ""
sleep 1s
echo "curl $dice -X POST --header 'Content-Type: application/json' --data $json2"
curl $dice -X POST --header 'Content-Type: application/json' --data $json2
echo ""
echo "curl $dice -X POST --header 'Content-Type: application/json' --data $json3"
curl $dice -X POST --header 'Content-Type: application/json' --data $json3
echo ""
sleep 4s
auth='user:password'

echo "Memory functions: Requires authentication"
echo "When called with a GET, this returns up to 20 previous stored rolls."
echo "The authentication is user:password."
echo "curl $memory -X GET"
curl $memory -X GET
echo ""
sleep 1s
echo "curl $memory -X GET -u $auth"
curl $memory -X GET -u $auth
echo ""
sleep 4s
postroll='{"name": "pew pew", "d8":10, "mod":10}'
patchroll="127.0.0.1:5000/rolls/2"
deleteroll="127.0.0.1"

echo "PATCH/POST/DELETE functionality"
echo "curl $rolls -X POST --header 'Content-Type: application/json' --data $json1"
curl $rolls -X POST --header 'Content-Type: application/json' --data $json1
echo ""
echo "curl $rolls -X POST --header 'Content-Type: application/json' --data $json2"
curl $rolls -X POST --header 'Content-Type: application/json' --data $json2
echo ""
echo "curl $rolls -X GET"
curl $rolls -X GET
echo ""
sleep 1s
echo "curl $patchroll -X PATCH --header 'Content-Type: application/json' --data $postroll"
curl $patchroll -X PATCH --header 'Content-Type: application/json' --data $postroll
echo "curl $rolls -X GET"
curl $rolls -X GET
echo ""
echo "curl $patchroll -X DELETE"
curl $patchroll -X DELETE
echo "curl $rolls -X GET"
curl $rolls -X GET
echo ""
sleep 4s