#!/usr/bin/perl

use warnings;
use strict;

##################################################################################### 
# This program provides an #include style capability for perl programs. There is
# undoubtedly a better perl way to do this, but I don't know what it is.
#
# Files that use the capability can contain the following commands at the left margin:
#     ### BEGIN INCLUDE <name>       - This is the start of a portion of code to include
#                                      when a DO INCLUDE <name> command is invoked
#     ### END INCLUDE <name>         - This the end of a portion of code to be included
#     ### DO INCLUDE <name> <file>   - Include the code associated with <name> found in
#                                      <file> here
#     ### DO NOT INCLUDE             - Temporarily suspend inclusion of code into the
#                                      current block
#     ### DO INCLUDE                 - Resume inclusion of code
# 
# Author: James Mayfield
# Please send questions or comments to jamesmayfield "at" gmail "dot" com
##################################################################################### 

binmode(STDOUT, ":utf8");

unless (@ARGV == 1) {
  print STDERR "Usage: perl $0 <file-with-inclusions>\n";
  exit 0;
}

{
  # Keep track of blocks of code to be included by <name>
  my %includes;

  # Load a library that contains INCLUDE commands
  sub load {
    my ($filename) = @_;
    # Only load each file once
    unless (defined $includes{$filename}) {
      open(my $infile, "<:utf8", $filename) or die "Could not open $filename: $!";
      # Current is the name of the block of code currently being defined
      my $current;
      # Are we appending lines of code to the $current block?
      my $including = 'true';
      while (<$infile>) {
	if (/^\s*#+\s*DO\s*NOT\s*INCLUDE\s*$/) {
	  die "Repeated DO NOT INCLUDEs" unless $including;
	  undef $including;
	}
	elsif (/^\s*#+\s*DO\s*INCLUDE\s*$/) {
	  die "Repeated DO INCLUDEs" if $including;
	  $including = 'true';
	}
	elsif ($including && /^\s*#+\s*BEGIN\s+INCLUDE\s+(\w+?)\s*$/) {
	  my $key = $1;
	  die "Nested include ($key inside $current in $filename" if defined $current;
	  $current = $key;
	}
	elsif ($including && /^\s*#+\s*END\s+INCLUDE\s+(\w+?)\s*$/) {
	  my $key = $1;
	  die "END INCLUDE $key without corresponding BEGIN" unless defined $current;
	  die "END INCLUDE $key closing BEGIN INCLUDE $current" unless $current eq $key;
	  undef $current;
	}
	elsif ($including && $current) {
	  $includes{$filename}{$current} .= $_;
	}
      }
      close $infile;
    }
    return $includes{$filename};
  }
}

# Process the INCLUDE commands in the master file
open(my $infile, "<:utf8", $ARGV[0]) or die "Could not open $ARGV[0]: $!";
my $including = 'true';
while (<$infile>) {
  # Support turning inclusion off and on in the master file
  if (/^\s*#+\s*DO\s*NOT\s*INCLUDE\s*$/) {
    die "Repeated DO NOT INCLUDEs" unless $including;
    undef $including;
  }
  elsif (/^\s*#+\s*DO\s*INCLUDE\s*$/) {
    die "Repeated DO INCLUDEs" if $including;
    $including = 'true';
  }
  # If a particular <name> has been requested for inclusion, include
  # all the relevant text here
  elsif ($including && /^\s*#+\s*DO\s+INCLUDE\s+(\w+?)\s+(.*?)\s*$/) {
    my $key = $1;
    my $includefile = $2;
    my $includes = &load($includefile);
    die "$key is not an inclusion specified in $includefile" unless $includes->{$key};
    print $includes->{$key};
    print "package main;\n";
  }
  elsif ($including) {
    print;
  }
}

1;
