package gorover

import (
	"context"
	"fmt"

	rpio "github.com/stianeikeland/go-rpio"
)

// Rover is the base struct for the Rover in Golang.
type Rover struct {
	rCTX   context.Context
	rTires []roverTire
}

type roverTire struct {
	tireEnable  rpio.Pin
	tireForward rpio.Pin
	tireReverse rpio.Pin
}

// NewRover -
func NewRover() *Rover {
	if err := rpio.Open(); err != nil {
		panic(fmt.Sprintf("could not open GPIO handle (%s)", err.Error()))
	}
	c := Rover{rTires: []roverTire{
		roverTire{rpio.Pin(18), rpio.Pin(23), rpio.Pin(24)},
		roverTire{rpio.Pin(25), rpio.Pin(06), rpio.Pin(12)},
		roverTire{rpio.Pin(17), rpio.Pin(22), rpio.Pin(27)},
		roverTire{rpio.Pin(16), rpio.Pin(05), rpio.Pin(13)},
	}}
	for _, t := range c.rTires {
		t.setup()
	}
	return &c
}

// Stop the Rover from moving.
func (r *Rover) Stop() {
	r.rTires[0].stop()
	r.rTires[3].stop()
	r.rTires[1].stop()
	r.rTires[2].stop()
}

// Left turns the Rover left.
func (r *Rover) Left() {
	r.rTires[1].forward()
	r.rTires[2].forward()
	r.rTires[0].reverse()
	r.rTires[3].reverse()
}

// Right turns the Rover right.
func (r *Rover) Right() {
	r.rTires[0].forward()
	r.rTires[3].forward()
	r.rTires[1].reverse()
	r.rTires[2].reverse()
}

// Forward moves the Rover forward.
func (r *Rover) Forward() {
	r.rTires[0].forward()
	r.rTires[1].forward()
	r.rTires[2].forward()
	r.rTires[3].forward()
}

// Reverse moves the Rover backward.
func (r *Rover) Reverse() {
	r.rTires[0].reverse()
	r.rTires[1].reverse()
	r.rTires[2].reverse()
	r.rTires[3].reverse()
}

func (t *roverTire) stop() {
	t.tireEnable.Low()
	t.tireForward.Low()
	t.tireReverse.Low()
}
func (t *roverTire) setup() {
	t.tireEnable.Output()
	t.tireForward.Output()
	t.tireReverse.Output()
	t.stop()
}
func (t *roverTire) forward() {
	t.tireEnable.High()
	t.tireForward.High()
	t.tireReverse.Low()
}
func (t *roverTire) reverse() {
	t.tireEnable.High()
	t.tireForward.Low()
	t.tireReverse.High()
}

func (r *Rover) setContext(x context.Context) {
	if x == nil {
		panic("nil Context")
	}
	if r.rCTX != nil {
		r.Stop()
		r.rCTX = nil
	}
	go func(r *Rover) {
		select {
		case <-r.rCTX.Done():
			r.Stop()
			r.rCTX = nil
		}
	}(r)
}

func (r *Rover) LeftContext(x context.Context) {
	r.setContext(x)
	r.Left()
}
func (r *Rover) RightContext(x context.Context) {
	r.setContext(x)
	r.Right()
}

func (r *Rover) FowardContext(x context.Context) {
	r.setContext(x)
	r.Forward()
}

func (r *Rover) ReverseContext(x context.Context) {
	r.setContext(x)
	r.Reverse()
}
