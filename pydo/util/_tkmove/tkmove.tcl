package provide tkmove 0.1
package require Tcl 8.6
package require Tk 8.6
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

	if {"${tcl_platform(platform)}" == "windows"} {
		# windows, so just update is fine
		proc wait_deiconify {window} {
			wm deiconify $window
			update
		}
	} else {
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

	# window, movefunc, targetx, targety, [weight [maxval]]
	proc move_to {window rawmove tx ty args} {
		set weight 1
		set maxval Inf
		set absmove 1
		foreach {flag val} $args {
			if {$flag == "-w"} {
				set weight $val
			} elseif {$flag == "-m"} {
				set maxval $val
			} elseif {$flag == "-a"} {
				set absmove $val
			} else {
				error "Unrecognized flag $flag"
			}
		}
		variable target [list \
			[expr "max(min([winfo screenwidth $window]-1, $tx), 0)"] \
			[expr "max(min([winfo screenheight $window]-1, $ty), 0)"]]
		variable curpos [winfo pointerxy $window]

		variable delta [list 0 0]
		variable steps 0
		while {"$curpos" != "$target"} {
			set delta ""
			foreach {cur} $curpos {tgt} $target {
				set dif [expr "(${tgt} - ${cur})*$weight"]
				if {$dif < 0} {
					lappend delta [expr "int(max(-$maxval, min(-1, $dif)))"]
				} elseif {$dif > 0} {
					lappend delta [expr "int(min($maxval, max(1, $dif)))"]
				} else {
					lappend delta 0
				}
			}
			puts "curpos: $curpos"
			puts "   idx: $steps"
			puts "    dx: $delta"
			eval "$rawmove $delta"
			update
			incr steps
			# Might be too quick if so many steps
			if {$steps > 100} {after [expr "$steps/10"]}
			set curpos [winfo pointerxy $window]
		}
	}
}
