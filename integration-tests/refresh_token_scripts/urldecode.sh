#!/usr/bin/env bash
urldecode() { : "${*//+/ }"; echo -e "${_//%/\\x}"; }
urldecode `cat token_encoded` > token.json
