package provide tkmove 0.1
package require Tcl 8.6
namespace eval ::tkmove {
	variable verbose 0
	proc enterred {window} {
		upvar "::tkmove::count_${window}" cfgcount
		if {$::tkmove::verbose} {
			puts -nonewline "E"
			flush stdout
		}
		if {${cfgcount} == 1 || ${cfgcount} == 4} {
			set "::tkmove::done_${window}" 0
		}
	}

	proc configured {window} {
		upvar "::tkmove::count_${window}" cfgcount
		set cfgcount [expr "${cfgcount}+1"]
		if {$::tkmove::verbose} {
			puts -nonewline "C"
			flush stdout
		}
	}

	proc moved {window} {
		upvar "::tkmove::count_${window}" cfgcount
		upvar "::tkmove::done_${window}" cfgdone
		set cfgdone 0
		if {$::tkmove::verbose} {
			puts -nonewline "M"
			flush stdout
		}
	}

	bind tkmovetag <Configure> "::tkmove::configured %W"
	bind tkmovetag <Enter> "::tkmove::enterred %W"
	bind tkmovetag <Motion> "::tkmove::moved %W"

	proc wait_deiconify {window} {
		# Leave window in topmost fullscreen.
		set "::tkmove::count_${window}" 0
		set "::tkmove::done_${window}" 0
		if {$::tkmove::verbose} {
			puts "wait_deiconify ${window}"
		}
		try {
			bindtags "${window}" [lappend [bindtags "${window}"] tkmovetag]
			wm attributes "${window}" -topmost true -fullscreen true
			wm deiconify "${window}"
			variable afterev [after 1000 [list set "::tkmove::done_${window}" 0]]
			vwait "::tkmove::done_${window}"
			after cancel ${afterev}
			if {$::tkmove::verbose} {
				puts ""
			}
		} finally {
			bindtags "${window}" [lrange [bindtags "${window}"] 0 end-1]
			unset "::tkmove::done_${window}"
			unset "::tkmove::count_${window}"
		}
	}
}
