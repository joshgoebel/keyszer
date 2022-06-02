

./bin/xkeysnail $@ &
PID=$!

function cleanup()
{
  kill $PID
}
trap cleanup EXIT
trap cleanup KILL


sleep 20
kill $PID
