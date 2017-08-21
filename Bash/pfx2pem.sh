if [ $# -ne 1 ]; then
  echo "Usage\npfx2pem <pfx>"
  exit 1
fi

cert=$1
openssl pkcs12 -in "$cert" -nocerts -out "/tmp/$cert.pem" -nodes
openssl pkcs12 -in "$cert" -nokeys -out "$cert-pem.pem"
openssl rsa -in "/tmp/$cert.pem" -out "$cert-key.key"
rm "/tmp/$cert.pem"
