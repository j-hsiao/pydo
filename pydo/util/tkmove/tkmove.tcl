package provide tkmove 0.1
package require Tcl 8.6
namespace eval ::tkmove {
	proc enterred {window} {
		upvar "::tkmove::count_${window}" cfgcount
		puts "enterred ${cfgcount}"
	}

	proc configured {window} {
		upvar "::tkmove::count_${window}" cfgcount
		set cfgcount [expr "${cfgcount}+1"]
		puts "configured ${cfgcount}"
	}

	proc moved {window} {
		upvar "::tkmove::count_${window}" cfgcount
		upvar "::tkmove::done_${window}" cfgdone
		puts "moved ${cfgcount}"
		set cfgdone 0
	}

	bind tkmovetag <Configure> "::tkmove::configured %W"
	bind tkmovetag <Enter> "::tkmove::enterred %W"
	bind tkmovetag <Motion> "::tkmove::moved %W"

	proc wait_deiconify {window} {
	# Leave window in topmost fullscreen.
		set "::tkmove::count_${window}" 0
		set "::tkmove::done_${window}" 0
		puts "wait_deiconify ${window}"
		try {
			bindtags ${window} [lappend [bindtags ${window}] tkmovetag]
			wm attributes $window -topmost true -fullscreen true
			wm deiconify $window
			after 1000 "set {::tkmove::done_${window}} 0"
			vwait "::tkmove::done_${window}"
			puts "wait done"
		} finally {
			bindtags ${window} [lrange [bindtags ${window}] 0 end-1]
			unset "::tkmove::done_${window}"
			unset "::tkmove::count_${window}"
		}
	}
}

::tkmove::wait_deiconify .
