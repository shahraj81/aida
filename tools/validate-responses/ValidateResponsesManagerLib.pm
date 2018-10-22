#!/usr/bin/perl

use warnings;
use strict;
use Encode;
use Carp;

### BEGIN INCLUDE Switches

# I don't know where this script will be run, so pick a reasonable
# screen width for describing program usage (with the -help switch)
my $terminalWidth = 80;

### END INCLUDE Switches

#####################################################################################
# Super
#####################################################################################

package Super;

sub set {
  my ($self, $field, @values) = @_;
  my $method = $self->can("set_$field");
  $method->($self, @values) if $method;
  $self->{$field} = $values[0] unless $method;
}

sub get {
  my ($self, $field, @arguments) = @_;
  return $self->{$field} if defined $self->{$field} && not scalar @arguments;
  my $method = $self->can("get_$field");
  return $method->($self, @arguments) if $method;
  return "nil";
}

sub get_BY_INDEX {
  my ($self) = @_;
  die "Abstract method 'get_BY_INDEX' not defined in derived class '", $self->get("CLASS") ,"'\n";
}

sub get_BY_KEY {
  my ($self) = @_;
  die "Abstract method 'get_BY_KEY' not defined in derived class '", $self->get("CLASS") ,"'\n";
}

sub increment {
	my ($self, $field, $increment_by) = @_;
	$increment_by = 1 unless $increment_by;
	$self->set($field, $self->get($field) + $increment_by);
}

sub has {
	my ($self, $key) = @_;
	$self->{$key};
}

sub dump_structure {
  my ($structure, $label, $indent, $history, $skip) = @_;
  if (ref $indent) {
    $skip = $indent;
    undef $indent;
  }
  my $outfile = *STDERR;
  $indent = 0 unless defined $indent;
  $history = {} unless defined $history;

  # Handle recursive structures
  if ($history->{$structure}) {
    print $outfile "  " x $indent, "$label: CIRCULAR\n";
    return;
  }

  my $type = ref $structure;
  unless ($type) {
    $structure = 'undef' unless defined $structure;
    print $outfile "  " x $indent, "$label: $structure\n";
    return;
  }
  if ($type eq 'ARRAY') {
    $history->{$structure}++;
    print $outfile "  " x $indent, "$label:\n";
    for (my $i = 0; $i < @{$structure}; $i++) {
      &dump_structure($structure->[$i], $i, $indent + 1, $history, $skip);
    }
  }
  elsif ($type eq 'CODE') {
    print $outfile "  " x $indent, "$label: CODE\n";
  }
  elsif ($type eq 'IO::File') {
    print $outfile "  " x $indent, "$label: IO::File\n";
  }
  else {
    $history->{$structure}++;
    print $outfile "  " x $indent, "$label:\n";
    my %done;
  outer:
    # You can add field names prior to the sort to order the fields in a desired way
    foreach my $key (sort keys %{$structure}) {
      if ($skip) {
  foreach my $skipname (@{$skip}) {
    next outer if $key eq $skipname;
  }
      }
      next if $done{$key}++;
      # Skip undefs
      next unless defined $structure->{$key};
      &dump_structure($structure->{$key}, $key, $indent + 1, $history, $skip);
    }
  }
}

#####################################################################################
# SuperObject
#####################################################################################

package SuperObject;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = {
    CLASS => 'SuperObject',
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

### BEGIN INCLUDE Logger

# The package Logger is taken with permission from James Mayfield's ColdStart library

#####################################################################################
# Reporting Problems
#####################################################################################

# The following is the default list of problems that can be checked
# for. A different list of problems can be specified as an argument to
# Logger->new(). WARNINGs can be corrected and do not prevent further
# processing. ERRORs permit further error checking, but processing
# does not proceed after that. FATAL_ERRORs cause immediate program
# termination when the error is reported.

my $problem_formats = <<'END_PROBLEM_FORMATS';

# Error Name                              Type           Error Message
# ----------                              ----           -------------

########## General Errors
  ACROSS_DOCUMENT_JUSTIFICATION           WARNING        Justification spans come from multiple documents (expected to be from document %s)
  DUPLICATE_QUERY                         DEBUG_INFO     Query %s (file: %s) is a duplicate of %s (file: %s) therefore skipping it
  DISCONNECTED_VALID_GRAPH                WARNING        Considering only valid edges, the graph in submission is not fully connected
  EXTRA_EDGE_JUSTIFICATIONS               WARNING        Extra edge justifications (expected <= %s; provided %s)
  INVALID_CONFIDENCE                      WARNING        Invalid confidence %s in response
  INVALID_END                             WARNING        Invalid end %s in response justification of type %s
  INVALID_JUSTIFICATION_TYPE              ERROR          Invalid justification type %s
  INVALID_KEYFRAMEID                      WARNING        Invalid keyframeid %s 
  INVALID_START                           WARNING        Invalid start %s in %s
  MISMATCHING_COLUMNS                     FATAL_ERROR    Mismatching columns (header:%s, entry:%s) %s %s
  MISSING_FILE                            FATAL_ERROR    Could not open %s: %s
  MISSING_MODALITY                        ERROR          Modality corresponding to encoding format %s not found
  MULTIPLE_POTENTIAL_ROOTS                FATAL_ERROR    Multiple potential roots "%s" in query DTD file: %s
  NONNUMERIC_END                          WARNING        End %s is not numeric
  NONNUMERIC_START                        WARNING        Start %s is not numeric
  UNDEFINED_FUNCTION                      FATAL_ERROR    Function %s not defined in package %s
  UNEXPECTED_ENTTYPE                      WARNING        Unexpected enttype %s in response (expected %s)
  UNEXPECTED_JUSTIFICATION_MODALITY       WARNING        Unexpected justification modality provided %s from document element %s of modality %s
  UNEXPECTED_JUSTIFICATION_SOURCE         WARNING        Justification(s) came from unexpected document(s) %s (expected to be from %s)
  UNEXPECTED_OUTPUT_TYPE                  FATAL_ERROR    Unknown output type %s
  UNEXPECTED_QUERY_TYPE                   FATAL_ERROR    Unexpected query type %s
  UNEXPECTED_SUBJECT_ENTTYPE              WARNING        Unexpected subject type %s (expected %s) in response to query %s and edge %s
  UNKNOWN_DOCUMENT                        WARNING        Unknown Document %s in response
  UNKNOWN_DOCUMENT_ELEMENT                WARNING        Unknown DocumentElement %s in response
  UNKNOWN_EDGEID                          WARNING        Unknown edge %s in response to query %s 
  UNKNOWN_QUERYID                         WARNING        Unknown query %s in response
END_PROBLEM_FORMATS


#####################################################################################
# Logger
#####################################################################################

package Logger;

use Carp;

# NIST submission scripts demand an error code of 255 on failure
our $NIST_error_code = 255;

# Create a new Logger object
sub new {
  my ($class, $formats, $error_output) = @_;
  $formats = $problem_formats unless $formats;
  my $self = {FORMATS => {}, PROBLEMS => {}, PROBLEM_COUNTS => {}};
  bless($self, $class);
  $self->set_error_output($error_output);
  $self->add_formats($formats);
  $self;
}

# Add additional error formats to an existing Logger
sub add_formats {
  my ($self, $formats) = @_;
  # Convert the problem formats list to an appropriate hash
  chomp $formats;
  foreach (grep {/\S/} grep {!/^\S*#/} split(/\n/, $formats)) {
    s/^\s+//;
    my ($problem, $type, $format) = split(/\s+/, $_, 3);
    $self->{FORMATS}{$problem} = {TYPE => $type, FORMAT => $format};
  }
}

# Get a list of warnings that can be ignored through the -ignore switch
sub get_warning_names {
  my ($self) = @_;
  join(", ", grep {$self->{FORMATS}{$_}{TYPE} eq 'WARNING'} sort keys %{$self->{FORMATS}});
}

# Do not report warnings of the specified type
sub ignore_warning {
  my ($self, $warning) = @_;
  $self->NIST_die("Unknown warning: $warning") unless $self->{FORMATS}{$warning};
  $self->NIST_die("$warning is a fatal error; cannot ignore it") unless $self->{FORMATS}{$warning}{TYPE} eq 'WARNING';
  $self->{IGNORE_WARNINGS}{$warning}++;
}

# Just use the ignore_warning mechanism to delete errors, but don't enforce the warnings-only edict
sub delete_error {
  my ($self, $error) = @_;
  $self->NIST_die("Unknown error: $error") unless $self->{FORMATS}{$error};
  $self->{IGNORE_WARNINGS}{$error}++;
}

# Is a particular error being ignored?
sub is_ignored {
  my ($self, $warning) = @_;
  $self->NIST_die("Unknown error: $warning") unless $self->{FORMATS}{$warning};
  $self->{IGNORE_WARNINGS}{$warning};
}

# Remember the debug information
sub record_debug_information {
	my ($self, $information, @args) = @_;
	my $source = pop(@args);
	my $format = $self->{FORMATS}{$information} ||
									{TYPE => 'DEBUG_INFO',
									FORMAT => "General information $information: %s"};
	my $type = $format->{TYPE};
	my $message = "$type: " . sprintf($format->{FORMAT}, @args);
	if ($type ne "DEBUG_INFO") {
		my ($package, $filename, $line) = caller;
	$self->record_problem("UNEXPECTED_RECORD_DEBUG_INFO_CALL", {FILENAME=>$filename, LINENUM=>$line});
	}
	# Use Encode to support Unicode.
	$message = Encode::encode_utf8($message);
	my $where = (ref $source ? "$source->{FILENAME} line $source->{LINENUM}" : $source);
	$self->{DEBUG_INFO}{$information}{$message}{$where}++;
}

# Remember that a particular problem was encountered, for later reporting
sub record_problem {
  my ($self, $problem, @args) = @_;
  my $source = pop(@args);
  # Warnings can be suppressed here; errors cannot
  return if $self->{IGNORE_WARNINGS}{$problem};
  my $format = $self->{FORMATS}{$problem} ||
               {TYPE => 'INTERNAL_ERROR',
		FORMAT => "Unknown problem $problem: %s"};
  my $type = $format->{TYPE};
  my $message = "$type: " . sprintf($format->{FORMAT}, @args);
  # Use Encode to support Unicode.
  $message = Encode::encode_utf8($message);
  my $where = (ref $source ? "$source->{FILENAME} line $source->{LINENUM}" : $source);
  $self->NIST_die("$message\n$where") if $type eq 'FATAL_ERROR' || $type eq 'INTERNAL_ERROR';
  $self->{PROBLEM_COUNTS}{$format->{TYPE}}++
		unless $self->{PROBLEMS}{$problem}{$message}{$where};
  $self->{PROBLEMS}{$problem}{$message}{$where}++;
}

# Send error output to a particular file or file handle
sub set_error_output {
  my ($self, $output) = @_;
  if (!$output) {
    $output = *STDERR{IO};
  }
  elsif (!ref $output) {
    if (lc $output eq 'stdout') {
      $output = *STDOUT{IO};
    }
    elsif (lc $output eq 'stderr') {
      $output = *STDERR{IO};
    }
    else {
      $self->NIST_die("File $output already exists") if -e $output;
      open(my $outfile, ">:utf8", $output) or $self->NIST_die("Could not open $output: $!");
      $output = $outfile;
      $self->{OPENED_ERROR_OUTPUT} = 'true';
    }
  }
  $self->{ERROR_OUTPUT} = $output
}

# Retrieve the file handle for error output
sub get_error_output {
  my ($self) = @_;
  $self->{ERROR_OUTPUT};
}

# Close the error output if it was opened here
sub close_error_output {
  my ($self) = @_;
  close $self->{ERROR_OUTPUT} if $self->{OPENED_ERROR_OUTPUT};
}

# Report all of the information that have been aggregated to the selected error output
sub report_all_information {
	my ($self) = @_;
	my $error_output = $self->{ERROR_OUTPUT};
	foreach my $log_item_category (qw(DEBUG_INFO PROBLEMS)) {
		foreach my $problem (sort keys %{$self->{$log_item_category}}) {
			foreach my $message (sort keys %{$self->{$log_item_category}{$problem}}) {
				my $num_instances = scalar keys %{$self->{$log_item_category}{$problem}{$message}};
				print $error_output "$message";
				my $example = (sort keys %{$self->{$log_item_category}{$problem}{$message}})[0];
				if ($example ne 'NO_SOURCE') {
					print $error_output " ($example";
					print $error_output " and ", $num_instances - 1, " other place" if $num_instances > 1;
					print $error_output "s" if $num_instances > 2;
					print $error_output ")";
				}
				print $error_output "\n";
			}
		}
	}
	# Return the number of errors and the number of warnings encountered
	($self->{PROBLEM_COUNTS}{ERROR} || 0, $self->{PROBLEM_COUNTS}{WARNING} || 0);
}

sub get_num_errors {
  my ($self) = @_;
  $self->{PROBLEM_COUNTS}{ERROR} || 0;
}

sub get_num_warnings {
  my ($self) = @_;
  $self->{PROBLEM_COUNTS}{WARNING} || 0;
}

sub get_error_type {
  my ($self, $error_name) = @_;
  $self->{FORMATS}{$error_name}{TYPE};
}

### DO NOT INCLUDE
# FIXME: Inconsistency: sometimes NIST_die is called directly; other
# times record_problem is called with a FATAL_ERROR
### DO INCLUDE
sub NIST_die {
  my ($self, @messages) = @_;
  print "Fatal error encountered.\n";
  my $outfile = $self->{ERROR_OUTPUT};
  print $outfile "================================================================\n";
  print $outfile Carp::longmess();
  print $outfile "================================================================\n";
  print $outfile join("", @messages), " at (", join(":", caller), ")\n";
  exit $NIST_error_code;
}

### END INCLUDE Logger

#####################################################################################
# Container
#####################################################################################

package Container;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $element_class) = @_;
  $element_class = "RAW" unless $element_class;
  my $self = {
    CLASS => 'Container',
    ELEMENT_CLASS => $element_class,
    STORE => {},
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub get_BY_INDEX {
  my ($self, $index) = @_;
  $self->{STORE}{LIST}[$index];
}

sub get_BY_KEY {
 	my ($self, $key) = @_;
	my $where = {FILENAME => __FILE__, LINENUM => __LINE__};
	unless($key) {
		$self->get("LOGGER")->record_problem("UNDEFINED_VARIABLE", "\$key", $where);
		return;
	}
	unless($self->{STORE}{TABLE}{$key}) {
	# Create an instance if not exists
		$self->get("LOGGER")->record_problem("MISSING_RAW_KEY", $key, $self->get("ELEMENT_CLASS"), $where)
			if $self->get("ELEMENT_CLASS") eq "RAW";
		my $element = $self->get("ELEMENT_CLASS")->new($self->get("LOGGER"));
		$self->add($element, $key);
	}
	$self->{STORE}{TABLE}{$key};
}

sub get_ALL_KEYS {
	my ($self) = @_;
	keys %{$self->{STORE}{TABLE}};
}

sub exists {
	my ($self, $key) = @_;
	exists $self->{STORE}{TABLE}{$key};
}

sub add {
	my ($self, $value, $key) = @_;
	if($value eq "KEY") {
		push(@{$self->{STORE}{LIST}}, $key);
		$self->{STORE}{TABLE}{$key} = $key;
	}
	elsif($key) {
		unless($self->{STORE}{TABLE}{$key}) {
			push(@{$self->{STORE}{LIST}}, $value);
			$self->{STORE}{TABLE}{$key} = $value;
		}
	}
	else {
		push(@{$self->{STORE}{LIST}}, $value);
		$key = @{$self->{STORE}{LIST}} - 1;
		$self->{STORE}{TABLE}{$key} = $value;
	}
}

sub toarray {
  my ($self) = @_;
  @{$self->{STORE}{LIST} || []};
}

sub display {
  my ($self) = @_;
  print $self->tostring();
}

sub tostring {
  my ($self) = @_;
  my $string = "";
  foreach my $element( $self->toarray() ){
    $string .= $element->tostring();
    $string .= "\n";
  }
  $string;
}

#####################################################################################
# File Handler
#####################################################################################

package FileHandler;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $filename) = @_;
  my $self = {
    CLASS => 'FileHandler',
    FILENAME => $filename,
    HEADER => undef,
    ENTRIES => Container->new($logger),
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load($filename);
  $self;
}

sub load {
  my ($self, $filename) = @_;

  my $linenum = 0;

  open(FILE, "<:utf8", $filename) or $self->get("LOGGER")->record_problem('MISSING_FILE', $filename, $!);
  my $line = <FILE>; 
  $line =~ s/\r\n?//g;
  chomp $line;

  $linenum++;

  $self->{HEADER} = Header->new($self->get("LOGGER"), $line);

  while($line = <FILE>){
    $line =~ s/\r\n?//g;
    $linenum++;
    chomp $line;
    my $entry = Entry->new($self->get("LOGGER"), $linenum, $line, $self->{HEADER}, 
    						{FILENAME => $filename, LINENUM => $linenum});
    $self->{ENTRIES}->add($entry);  
  }
  close(FILE);
}

sub display_header {
  my ($self) = @_;

  print $self->{HEADER}->tostring();  
}

sub display_entries {
  my ($self) = @_;

  print $self->{ENTRIES}->tostring();
}

sub cleanup {
	my ($self) = @_;
	delete $self->{ENTRIES};
}

sub display {
  my ($self) = @_;

  print "HEADER: \n";
  print $self->display_header();
  print "\n";
  print "ENTRIES: \n";
  print $self->display_entries();
  print "\n"; 
}

#####################################################################################
# Header
#####################################################################################

package Header;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $line, $field_separator) = @_;
  $field_separator = "\t" unless $field_separator;
  my $self = {
    CLASS => 'Header',
    ELEMENTS => [],
    FIELD_SEPARATOR => $field_separator,
    LINE => $line,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load($line);
  $self;
}

sub load {
  my ($self, $line) = @_;
  my $field_separator = $self->get("FIELD_SEPARATOR");
  @{$self->{ELEMENTS}} = split( /$field_separator/, $line);
}

sub get_NUM_OF_COLUMNS {
  my ($self) = @_;
  scalar @{$self->{ELEMENTS}};
}

sub get_ELEMENT_AT {
  my ($self, $at) = @_;

  $self->{ELEMENTS}[$at];
}

sub tostring {
  my ($self) = @_;
  my $i=0;
  my $string = "";
  my $num_of_columns = $self->get("NUM_OF_COLUMNS");
  foreach my $i( 0..$num_of_columns-1 ){
     my $element = $self->get("ELEMENT_AT", $i);
    $string = $string ."$i . $element\n";
    $i++;
  }
  $string;
}

#####################################################################################
# Entry
#####################################################################################

package Entry;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $linenum, $line, $header, $where, $field_separator) = @_;
  $field_separator = "\t" unless $field_separator;
  my $self = {
    CLASS => 'Entry',
    LINENUM => $linenum,
    LINE => $line,
    HEADER => $header,
    ELEMENTS => [],
    MAP => {},
    FIELD_SEPARATOR => $field_separator,
    WHERE => $where,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->add($line, $header);
  $self;
}

sub get {
  my ($self, $field, @arguments) = @_;
  return $self->{$field} if defined $self->{$field} && not scalar @arguments;
  return $self->{MAP}{$field} if defined $self->{MAP}{$field} && not scalar @arguments;
  my $method = $self->can("get_$field");
  return $method->($self, @arguments) if $method;
  return;
}

sub add {
  my ($self, $line, $header) = @_;
  $line .= "\tEND";
  my $field_separator = $self->get("FIELD_SEPARATOR");
  @{$self->{ELEMENTS}} = split( /$field_separator/, $line);
  my $end = pop @{$self->{ELEMENTS}};
  %{$self->{MAP}} = map {$header->get("ELEMENT_AT",$_) => $self->get("ELEMENT_AT",$_)} (0..$header->get("NUM_OF_COLUMNS")-1);
}

sub get_NUM_OF_COLUMNS {
  my ($self) = @_;
  scalar @{$self->{ELEMENTS}};
}

sub get_ELEMENT_AT {
  my ($self, $at) = @_;
  $self->{ELEMENTS}[$at];
}

sub get_CATEGORY {
	my ($self) = @_;
	my $category = "n/a";
	$category = "ENTITY" if $self->get("entitymention_id");
	$category = "EVENT" if $self->get("eventmention_id");
	$category = "RELATION" if $self->get("relationmention_id");	
	$category;
}

sub get_nodemention_id {
	my ($self) = @_;
	my $nodemention_id;
	
	$nodemention_id = $self->get("entitymention_id") if $self->get("entitymention_id");
	$nodemention_id = $self->get("eventmention_id") if $self->get("eventmention_id");
	$nodemention_id = $self->get("relationmention_id") if $self->get("relationmention_id");
	$nodemention_id = $self->get("relation_event_mention_id") if $self->get("relation_event_mention_id");
	
	$nodemention_id;
}

sub get_document_level_node_id {
	my ($self) = @_;
	my $node_id;
	
	$node_id = $self->get("entity_id") if $self->get("entity_id");
	$node_id = $self->get("event_id") if $self->get("event_id");
	$node_id = $self->get("relation_id") if $self->get("relation_id");
	
	$node_id;
}

sub tostring {
  my ($self) = @_;

  my $num_of_columns_header = $self->get("HEADER")->get("NUM_OF_COLUMNS");
  my $num_of_columns_entry  = $self->get("NUM_OF_COLUMNS");
  my $header_line = $self->get("HEADER")->get("LINE");
	my $entry_line = $self->get("LINE");
  $self->get("LOGGER")->record_problem("MISMATCHING_COLUMNS", 
  												$num_of_columns_header, 
  												$num_of_columns_entry,
  												"\nHEADER: ==>$header_line<==\n",
  												"\nENTRY: ==>$entry_line<==\n",
  												$self->get("WHERE"))
		if ($num_of_columns_header != $num_of_columns_entry);

  my $string = "";

  foreach my $i(0..$num_of_columns_header-1) {
    $string = $string . $self->get("HEADER")->get("ELEMENT_AT", $i);
    $string = $string . ": "; 
    $string = $string . $self->get("ELEMENT_AT", $i);
    $string = $string . "\n";
  }

  $string;
}

#####################################################################################
# Parameters
#####################################################################################

package Parameters;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = {
    CLASS => 'Parameters',
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub get_GRAPH_QUERIES_PREFIX {
	my ($self) = @_;
	my $query_id_prefix = $self->get("GRAPH_QUERIES_SUBPREFIX");
	$query_id_prefix .= "_" . $self->get("HYPOTHESISID");
	$query_id_prefix;
}

sub get_EDGE_QUERIES_PREFIX {
	my ($self) = @_;
	my $query_id_prefix = $self->get("EDGE_QUERIES_SUBPREFIX");
	$query_id_prefix .= "_" . $self->get("HYPOTHESISID");
	$query_id_prefix;
}

#####################################################################################
# DTD
#####################################################################################

package DTD;

use parent -norequire, 'Super';

sub new {
	my ($class, $logger, $filename) = @_;
	
	my $self = {
		CLASS => 'DTD',
		LOGGER => $logger,
		FILENAME => $filename,
		TREE => Tree->new($logger, $filename),
	};
	bless($self, $class);
	$self->load();
	$self;
}

sub load {
	my ($self) = @_;
	
	my $filename = $self->get("FILENAME");
	open(FILE, "<:utf8", $filename) or $self->get("LOGGER")->record_problem('MISSING_FILE', $filename, $!);
	my $linenum = 0;
	while(my $line = <FILE>) {
		chomp $line;
		$linenum++;
		if(my ($parent, $children) = $line =~ /\<\!ELEMENT (.*?) \((.*?)\)\>/) {
			my $child_num = 0;
			foreach my $types(split(/,/, $children)) {
				$child_num++;
				my $modifier = 1;
				if($types =~ /\+$/) {
					$modifier = "+";
					$types =~ s/\+$//;
				}
				if($types =~ /^\((.*?)\)$/){
					$types = $1;
				}
				foreach my $type(split(/\|/, $types)) {
					$self->get("TREE")->add("CHILD", $parent, $child_num, $type, $modifier, {FILENAME=>$filename, LINENUM=>$linenum});
				}
			}
		}
		elsif(my ($node_id, $attribute) = $line =~ /\<\!ATTLIST (.*?) (.*?) .*?\>/) {
			$self->get("TREE")->add("ATTRIBUTE", $node_id, $attribute);
		}
	}
	$self->determine_root();
	close(FILE);
}

sub determine_root {
	my ($self) = @_;
	$self->get("TREE")->get("ROOT");
}

sub get_ROOT {
	my ($self) = @_;
	$self->get("TREE")->get("ROOT");
}

sub tostring {
	my ($self, $indent) = @_;
	$self->get("TREE")->tostring();
}

#####################################################################################
# Tree
#####################################################################################

package Tree;

use parent -norequire, 'Super';

sub new {
	my ($class, $logger, $filename) = @_;
	
	my $self = {
		CLASS => 'Tree',
		LOGGER => $logger,
		FILENAME => $filename,
		ROOT => undef,
		POTENTIAL_ROOTS => [],
		NODES => Nodes->new($logger),
	};
	bless($self, $class);
	$self;
}

sub add {
	my ($self, $field, @arguments) = @_;
	my $method = $self->can("add_$field");
	my $where = {FILENAME => __FILE__, LINENUM => __LINE__};
	$self->get("LOGGER")->record_problem("UNDEFINED_FUNCTION", "add(\"$field\",...)", "Node", $where)
		unless $method;
	$method->($self, @arguments);
}

sub add_CHILD {
	my ($self, $parent_id, $child_num, $child_type_id, $child_modifier, $where) = @_;
	my $parent_node = $self->get("NODES")->get("BY_KEY", $parent_id);
	$parent_node->set("NODEID", $parent_id);
	my $type_node = $self->get("NODES")->get("BY_KEY", $child_type_id);
	$parent_node->set("CHILD_TYPES_MODIFIER", $child_num, $child_type_id, $child_modifier);	
	$type_node->add("PARENT", $parent_node);
}

sub add_ATTRIBUTE {
	my ($self, $node_id, $attribute) = @_;
	$self->get("NODES")->get("BY_KEY", $node_id)->add("ATTRIBUTE", $attribute);
}

sub get_ROOT {
	my ($self) = @_;
	return $self->get("ROOT") if $self->{ROOT};
	my $filename = $self->get("FILENAME");
	foreach my $node($self->get("NODES")->toarray()) {
		push (@{$self->get("POTENTIAL_ROOTS")}, $node) unless $node->has_parents();
	}
	my @potential_roots = @{$self->get("POTENTIAL_ROOTS")};
	my $potential_roots_ids_string = join(",", map {$_->get("NODEID")} @potential_roots);
	my $where = {FILENAME => __FILE__, LINENUM => __LINE__};
	$self->get("LOGGER")->record_problem("MULTIPLE_POTENTIAL_ROOTS", $potential_roots_ids_string, $filename, $where)
		if scalar @potential_roots > 1;
	$self->set("ROOT", $potential_roots[0]);
	$potential_roots[0];
}

sub get_NODE {
	my ($self, $node_id) = @_;
	$self->get("NODES")->get("BY_KEY", $node_id);
}

sub tostring {
	my ($self, $indent) = @_;
	my $retVal = "";
	foreach my $node($self->get("NODES")->toarray()) {
		$retVal .= $node->tostring();
	}
	$retVal;
}

#####################################################################################
# Nodes
#####################################################################################

package Nodes;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $parameters) = @_;
  my $self = $class->SUPER::new($logger, 'Node');
  $self->{CLASS} = 'Nodes';
  $self->{PARAMETERS} = $parameters;
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

#####################################################################################
# Node
#####################################################################################

package Node;

use parent -norequire, 'Super';

sub new {
	my ($class, $logger, $node_id) = @_;
	my $self = {
		CLASS => 'Node',
		NODEID => $node_id,
		PARENTS => Nodes->new($logger),
		CHILDNUM_TYPES_MAPPING => {},
		CHILDNUM_MODIFIER_MAPPING => {},
		ATTRIBUTES => Container->new($logger, "RAW"),
		TYPES => Container->new($logger, "RAW"),
		LOGGER => $logger,
	};
	bless($self, $class);
	$self;
}

sub add {
	my ($self, $field, @arguments) = @_;
	my $method = $self->can("add_$field");
	my $where = {FILENAME => __FILE__, LINENUM => __LINE__};
	$self->get("LOGGER")->record_problem("UNDEFINED_FUNCTION", "add(\"$field\",...)", "Node", $where)
		unless $method;
	$method->($self, @arguments);
}

sub add_PARENT {
	my ($self, $parent) = @_;
	$self->get("PARENTS")->add($parent, $parent->get("NODEID"));
}

#sub add_CHILD {
#	my ($self, $child) = @_;
#	$self->get("CHILDREN")->add($child, $child->get("NODEID"));
#}

#sub add_TYPE {
#	my ($self, $type) = @_;
#	$self->get("TYPES")->add("KEY", $type);
#}

sub add_ATTRIBUTE {
	my ($self, $attribute) = @_;
	my $i = scalar $self->get("ATTRIBUTES")->toarray();
	$self->get("ATTRIBUTES")->add($attribute, $i+1);
}

sub get_CHILDNUM_TYPES {
	my ($self, $child_num) = @_;
	keys %{$self->{CHILDNUM_TYPES_MAPPING}{$child_num}};
}

sub get_CHILDNUM_MODIFIER {
	my ($self, $child_num) = @_;
	$self->{CHILDNUM_MODIFIER_MAPPING}{$child_num};
}

sub get_NUM_OF_CHILDREN {
	my ($self) = @_;
	scalar keys %{$self->{CHILDNUM_MODIFIER_MAPPING}};
}

sub set_CHILD_TYPES_MODIFIER {
	my ($self, $child_num, $child_type_id, $child_modifier) = @_;
	$self->{CHILDNUM_TYPES_MAPPING}{$child_num}{$child_type_id} = 1;
	$self->{CHILDNUM_MODIFIER_MAPPING}{$child_num} = $child_modifier;
}

sub has_parents {
	my ($self) = @_;
	my $retVal = scalar $self->get("PARENTS")->toarray();
	$retVal;
}

sub is_leaf {
	my ($self) = @_;
	scalar keys %{$self->{CHILDNUM_MODIFIER_MAPPING}} == 0;
}

sub tostring {
	my ($self) = @_;
	my $attributes = join(",", $self->get("ATTRIBUTES")->toarray()) 
		if scalar $self->get("ATTRIBUTES")->toarray();
	$attributes = " attributes=$attributes" if $attributes;
	my $retVal = $self->get("NODEID") . ": ";
	foreach my $child_num(sort {$a<=>$b} keys %{$self->{CHILDNUM_TYPES_MAPPING}}) {
		my $child_modifier = $self->get("CHILDNUM_MODIFIER", $child_num);
		my @types = $self->get("CHILDNUM_TYPES", $child_num);
		my $types = join("|", @types);
		if(scalar @types > 1) {
			$retVal .= "(" . $types . ")";
		}
		else {
			$retVal .= $types;
		}
		$retVal .= "+" if($child_modifier eq "+");
		$retVal .= " ";
	}
	$retVal .= " $attributes\n";
	$retVal;
}

#####################################################################################
# XMLFileHandler
#####################################################################################

package XMLFileHandler;

use parent -norequire, 'Super';

sub new {
	my ($class, $logger, $dtd_filename, $xml_filename) = @_;
	my $self = {
		CLASS => "XMLFileHandler",
		DTD => DTD->new($logger, $dtd_filename),
		DTD_FILENAME => $dtd_filename,
		XML_FILENAME => $xml_filename,
		XML_FILEHANDLE => undef,
		LINENUM => -1,
		OBJECT_WHERE => undef,
		LOGGER => $logger,
	};
	bless($self, $class);
	$self->setup();
	$self;
}

sub setup {
	my ($self) = @_;
	open(my $filehandle, "<:utf8", $self->get("XML_FILENAME"));
	$self->set("XML_FILEHANDLE", $filehandle);
}

sub get_NEXT_OBJECT {
	my ($self) = @_;
	my ($search_tag) = $self->get("DTD")->get("ROOT")->get("CHILDNUM_TYPES", 1);
	my $search_node = $self->get("DTD")->get("TREE")->get("NODES")->get("BY_KEY", $search_tag);
	my $filehandle = $self->get("XML_FILEHANDLE");
	my $object_string = "";
	my $working = 0;
	my $done = 0;
	my $found = 0;
	while(my $line = <$filehandle>){
		$self->increment("LINENUM", 1);
		chomp $line;
		if($line =~ /(<$search_tag>|<$search_tag .*?=.*?>)/) {
			$self->set("OBJECT_WHERE", {FILENAME=>$self->get("XML_FILENAME"), LINENUM=>$self->get("LINENUM")});
			$working = 1;
			$object_string .= "$line\n";
		}
		elsif($line =~ /<\/$search_tag>/) {
			$working = 0;
			$object_string .= "$line\n";
			$found = 1;
			last;
		}
		elsif($working == 1) {
			$object_string .= "$line\n";
		}
	}
	return unless $found;
	$self->get("STRING_TO_OBJECT", $object_string, $search_node);
}

sub get_STRING_TO_OBJECT {
	my ($self, $object_string, $search_node) = @_;
	my $logger = $self->get("LOGGER");
	my $search_tag = $search_node->get("NODEID");
	my $num_of_children = $search_node->get("NUM_OF_CHILDREN");
	if($num_of_children == 1 && $search_node->get("CHILDNUM_MODIFIER", 1) eq "1") {
		# There is only one child and it appears only once
		# This is the base case of this recursive function
		my ($child_id) = $search_node->get("CHILDNUM_TYPES", 1);
		my $child_node = $self->get("DTD")->get("TREE")->get("NODE", $child_id);
		if($child_node->is_leaf()){
			# The child appears once and its a leaf
			# This serves as the base case for recursion
			if($object_string =~ /(<$search_tag>|<$search_tag .*?=.*?>)\s*(.*?)\s*<\/$search_tag>/gs){
				my ($attributes, $value) = ($1, $2);
				($attributes) = $attributes =~ /<$search_tag(.*?)>/;
				my $xml_attributes;
				if($attributes) {
					$xml_attributes = XMLAttributes->new($logger);
					while($attributes =~ /\s*(.*?)\s*=\s*\"(.*?)\"/g){
						my ($key, $value) = ($1, $2);
						$xml_attributes->add($value, $key);
					}
				}
				my $new_line = 0;
				if($search_tag eq "sparql") {
					$value = "\t$value\n";
					$new_line = 1;
				}
				return XMLElement->new($logger, $value, $search_tag, $new_line, $xml_attributes, $self->get("OBJECT_WHERE"));
			}
			else{
				# TODO: did not find the pattern we were expecting; throw an exception here
			}
		}
		else {
		# The child appears once but it is not a leaf node
			if($object_string =~ /(<$search_tag>|<$search_tag .*?=.*?>)\s*(.*?)\s*<\/$search_tag>/gs){
				my ($attributes, $new_object_string) = ($1, $2);
				($attributes) = $attributes =~ /<$search_tag(.*?)>/;
				my $xml_attributes;
				if($attributes) {
					$xml_attributes = XMLAttributes->new($logger);
					while($attributes =~ /\s*(.*?)\s*=\s*\"(.*?)\"/g){
						my ($key, $value) = ($1, $2);
						$xml_attributes->add($value, $key);
					}
				}
				my $xml_child_object = $self->get("STRING_TO_OBJECT", $new_object_string, $child_node);
				return XMLElement->new($logger, $xml_child_object, $search_tag, 1, $xml_attributes, $self->get("OBJECT_WHERE"));
			}
			else{
				# TODO: did not find the pattern we were expecting; throw an exception here
			}
		}
	}
	else {
		# First obtain the attributes and then unwrap $search_tag
		my ($attributes, $new_object_string) = $object_string =~ /(<$search_tag>|<$search_tag .*?=.*?>)\s*(.*?)\s*<\/$search_tag>/gs;
		($attributes) = $attributes =~ /<$search_tag(.*?)>/;
		$object_string = $new_object_string;
		$new_object_string = "";
		# Handle multiple children case
		my $looking_for_child_num = 1;
		# $done = 0: we have not found all children yet
		# $done = 1: found all children, move on
		my $done = 0;
		# $found = 0: the start of the tag not found yet
		# $found = 1: start-tag found but the end-tag is not
		my $found = 0;
		my $xml_container = XMLContainer->new($logger);
		my $new_search_tag;
		foreach my $line(split(/\n/, $object_string)){
			chomp $line;
process_next_child:
			# Get allowed types for this child
			my @this_child_allowed_types = $search_node->get("CHILDNUM_TYPES", $looking_for_child_num);
			my $this_child_modifier = $search_node->get("CHILDNUM_MODIFIER", $looking_for_child_num);
			# Get next child allowed types (undef)
			my @next_child_allowed_types = $search_node->get("CHILDNUM_TYPES", $looking_for_child_num+1);
			if(not $found) {
				# start not found
				# see if you find one of the allowed types for this child
				my $check_next_child = 1;
				foreach my $this_child_allowed_type(@this_child_allowed_types) {
					if($line =~ /\<$this_child_allowed_type.*?>/) {
						$new_search_tag = $this_child_allowed_type;
						$new_object_string = $line;
						$found = 1;
						$check_next_child = 0;
						# Handle cases like <tag.*?> value <\/tag>
						if($line =~ /\<\/$new_search_tag\>/) {
							my $child_node = $self->get("DTD")->get("TREE")->get("NODE", $this_child_allowed_type);
							my $xml_child_object = $self->get("STRING_TO_OBJECT", $new_object_string, $child_node);
							$xml_container->add($xml_child_object);
							$new_object_string = "";
							# Found the end; reset $found
							$found = 0;
						}
					}
				}
				if($check_next_child) {
					# allowed types for this child not found
					# see if what you found is the next child
					foreach my $next_child_allowed_type(@next_child_allowed_types) {
						if($line =~ /\<$next_child_allowed_type.*?>/) {
							$looking_for_child_num++;
							goto process_next_child;
						}
					}
				}
			}
			else {
				# start of the next child has been found but the end is not, find the end
				if($line =~ /\<\/$new_search_tag\>/) {
					# end found
					$new_object_string .= "\n$line";
					my $child_node = $self->get("DTD")->get("TREE")->get("NODE", $new_search_tag);
					my $xml_child_object = $self->get("STRING_TO_OBJECT", $new_object_string, $child_node);
					$xml_container->add($xml_child_object);
					$new_object_string = "";
					# Found the end; reset $found
					$found = 0;
				}
				else{
					$new_object_string .= "\n$line";
				}
			}
		}
		my $xml_attributes;
		if($attributes) {
			$xml_attributes = XMLAttributes->new($logger);
			while($attributes =~ /\s*(.*?)\s*=\s*\"(.*?)\"/g){
				my ($key, $value) = ($1, $2);
				$xml_attributes->add($value, $key);
			}
		}
		return XMLElement->new($logger, $xml_container, $search_tag, 1, $xml_attributes, $self->get("OBJECT_WHERE"));
	}
}

#####################################################################################
# XMLAttributes
#####################################################################################

package XMLAttributes;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = {
  	CLASS => 'XMLAttributes',
  	LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub tostring {
	my ($self) = @_;
	my $retVal = " ";
	join (" ", map {"$_=\"".$self->get('BY_KEY', $_)."\""} ($self->get("ALL_KEYS")));
}

#####################################################################################
# XMLElement
#####################################################################################

package XMLElement;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $element, $name, $newline, $attributes, $where) = @_;
  my $self = {
    CLASS => 'XMLElement',
    NAME => $name,
    NEWLINE => $newline,
    ATTRIBUTES => $attributes,
    ELEMENT => $element,
    WHERE => $where,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub get_OPENTAG {
	my ($self) = @_;

	my $attributes = "";
	$attributes = " " . $self->get("ATTRIBUTES")->tostring() if $self->get("ATTRIBUTES") ne "nil";

	"<" . $self->get("NAME") . $attributes . ">";
}

sub get_CLOSETAG {
	my ($self) = @_;

	"<\/" . $self->get("NAME") . ">";
}

sub get_CHILD {
	my ($self, $childname) = @_;

	return $self if($self->get("NAME") eq $childname);
	return $self->get("ELEMENT")->get("CHILD", $childname) if ref $self->get("ELEMENT");
	return unless ref $self->get("ELEMENT");
}

sub tostring {
	my ($self, $indent) = @_;
	return "" if $self->get("IGNORE") eq "1";
	$indent = 0 unless $indent;
	my $retVal = " " x $indent;
	$retVal .= $self->get("OPENTAG");
	$retVal .= "\n" if $self->get("NEWLINE");
	$retVal .= $self->get("ELEMENT")->tostring($indent+2) if ref $self->get("ELEMENT");
	$retVal .= " " . Encode::encode_utf8($self->get("ELEMENT")) . " " unless ref $self->get("ELEMENT");
	$retVal .= "\n" if $self->get("ELEMENT") eq "";
	$retVal .= " " x $indent if $self->get("NEWLINE");
	$retVal .= $self->get("CLOSETAG");
	$retVal .= "\n";
	$retVal;
}

#####################################################################################
# XMLContainer
#####################################################################################

package XMLContainer;

use parent -norequire, 'Container', 'Super';

sub new {
	my ($class, $logger, @xml_elements) = @_;
	my $self = $class->SUPER::new($logger, 'XMLElement');
	$self->{CLASS} = 'XMLContainer';
	$self->{LOGGER} = $logger;
	bless($self, $class);
	foreach my $xml_element(@xml_elements) {
		$self->add($xml_element);
	}
	$self;
}

sub get_CHILD {
	my ($self, $childname) = @_;
	my $child;
	foreach my $xml_element($self->toarray()){
		$child = $xml_element->get("CHILD", $childname);
		last if $child;
	}
	$child;
}

sub tostring {
	my ($self, $indent) = @_;
	my $retVal = "";
	foreach my $xml_elements($self->toarray()) {
		$retVal .= $xml_elements->tostring($indent);
	}
	$retVal;
}

#####################################################################################
# ResponseSet
#####################################################################################

package ResponseSet;

use parent -norequire, 'Super';

sub new {
	my ($class, $logger, $queries, $docid_mappings, $dtd_filename, $xml_filename) = @_;
	my $self = {
		CLASS => 'ResponseSet',
		QUERIES => $queries,
		DTD_FILENAME => $dtd_filename,
		XML_FILENAME => $xml_filename,
		DOCID_MAPPINGS => $docid_mappings, 
		RESPONSES => Container->new($logger, "Response"),
		LOGGER => $logger,
	};
	bless($self, $class);
	$self->load();
	$self;
}

sub load {
	my ($self) = @_;
	my $logger = $self->get("LOGGER");
	my $dtd_filename = $self->get("DTD_FILENAME");
	my $xml_filename = $self->get("XML_FILENAME");
	my $query_type = $self->get("QUERIES")->get("QUERYTYPE");
	my $docid_mappings = $self->get("DOCID_MAPPINGS");
	my $queries = $self->get("QUERIES");
	my $xml_filehandler = XMLFileHandler->new($logger, $dtd_filename, $xml_filename);
	my $i = 0;
	while(my $xml_response_object = $xml_filehandler->get("NEXT_OBJECT")) {
		$i++;
		my $response;
		$response = ClassResponse->new($logger, $xml_response_object, $xml_filename, $queries, $docid_mappings) if($query_type eq "class_query");
		$response = ZeroHopResponse->new($logger, $xml_response_object, $xml_filename, $queries, $docid_mappings) if($query_type eq "zerohop_query");
		$response = GraphResponse->new($logger, $xml_response_object, $xml_filename, $queries, $docid_mappings) if($query_type eq "graph_query");
		$self->get("RESPONSES")->add($response, $i) if $response->is_valid();
	}
}

sub tostring {
	my ($self, $indent) = @_;
	return "" unless $self->get("RESPONSES")->toarray(); 
	my $output_type = $self->get("DTD_FILENAME");
	$output_type =~ s/^(.*?\/)+//g;
	$output_type =~ s/.dtd//;
	my $retVal = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
	$retVal .= "<classquery_responses>\n" if($output_type eq "class_response");
	$retVal .= "<zerohopquery_responses>\n" if($output_type eq "zerohop_response");
	$retVal .= "<graphqueries_responses>\n" if($output_type eq "graph_response");
	foreach my $response($self->get("RESPONSES")->toarray()) {
		$retVal .= $response->tostring($indent);
	}
	$retVal .= "<\/classquery_responses>\n" if($output_type eq "class_response");
	$retVal .= "<\/zerohopquery_responses>\n" if($output_type eq "zerohop_response");
	$retVal .= "<\/graphqueries_responses>\n" if($output_type eq "graph_response");
	$retVal;
}

#####################################################################################
# ClassResponse
#####################################################################################

package ClassResponse;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $xml_object, $xml_filename, $queries, $docid_mappings) = @_;
  my $self = {
    CLASS => 'ClassResponse',
    XML_FILENAME => $xml_filename,
    XML_OBJECT => $xml_object,
    DOCID_MAPPINGS => $docid_mappings,
    QUERIES => $queries,
    QUERYID => undef,
    RESPONSE_DOCID => undef,
    JUSTIFICATIONS => undef,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load();
  $self;
}

sub load {
	my ($self) = @_;
	my $logger = $self->get("LOGGER");
	my $query_id = $self->get("XML_OBJECT")->get("ATTRIBUTES")->get("BY_KEY", "QUERY_ID");
	$self->set("QUERYID", $query_id);
	my $justifications = Container->new($logger, "Justification");
	my $i = 0;
	foreach my $justification_xml_object($self->get("XML_OBJECT")->get("CHILD", "justifications")->get("ELEMENT")->toarray()){
		$i++;
		my $justification;
		my $doceid = $justification_xml_object->get("CHILD", "doceid")->get("ELEMENT");
		my $justification_type = uc $justification_xml_object->get("NAME");
		my $where = $justification_xml_object->get("WHERE");
		my $enttype = $justification_xml_object->get("CHILD", "enttype")->get("ELEMENT");
		my $confidence = $justification_xml_object->get("CHILD", "confidence")->get("ELEMENT");
		my ($keyframeid, $start, $end);
		if($justification_xml_object->get("NAME") eq "text_justification") {
			$start = $justification_xml_object->get("CHILD", "start")->get("ELEMENT");
			$end = $justification_xml_object->get("CHILD", "end")->get("ELEMENT");
		}
		elsif($justification_xml_object->get("NAME") eq "video_justification") {
			$keyframeid = $justification_xml_object->get("CHILD", "keyframeid")->get("ELEMENT");
			$start = $justification_xml_object->get("CHILD", "topleft")->get("ELEMENT");
			$end = $justification_xml_object->get("CHILD", "bottomright")->get("ELEMENT");
		}
		elsif($justification_xml_object->get("NAME") eq "image_justification") {
			$start = $justification_xml_object->get("CHILD", "topleft")->get("ELEMENT");
			$end = $justification_xml_object->get("CHILD", "bottomright")->get("ELEMENT");
		}
		elsif($justification_xml_object->get("NAME") eq "audio_justification") {
			$start = $justification_xml_object->get("CHILD", "start")->get("ELEMENT");
			$end = $justification_xml_object->get("CHILD", "end")->get("ELEMENT");
		}
		$justification = Justification->new($logger, $justification_type, $doceid, $keyframeid, $start, $end, $enttype, $confidence, $justification_xml_object, $where);
		$justifications->add($justification, $i);
	}
	$self->set("JUSTIFICATIONS", $justifications);
}

sub parse_object {
	my ($self, $xml_object) = @_;
	my $logger = $self->get("LOGGER");
	my $retVal;
	if($xml_object->get("CLASS") eq "XMLElement" && !ref $xml_object->get("ELEMENT")) {
		# base-case of recursive function
		my $key = uc($xml_object->get("NAME"));
		my $value = $xml_object->get("ELEMENT");
		if($xml_object->get("ATTRIBUTES") ne "nil") {
			$retVal = SuperObject->new($logger);
			$retVal->set($key, $value);
			foreach my $attribute_key($xml_object->get("ATTRIBUTES")->get("ALL_KEYS")) {
				my $attribute_value = $xml_object->get("ATTRIBUTES")->get("BY_KEY", $attribute_key);
				$retVal->set($attribute_key, $attribute_value);
			}
		}
		else {
			$retVal = $value;
		}
	}
	else {
		if($xml_object->get("CLASS") eq "XMLElement") {
			my $key = uc($xml_object->get("NAME"));
			my $value = $self->parse_object($xml_object->get("ELEMENT"));
			$retVal = SuperObject->new($logger);
			$retVal->set($key, $value);
			if($xml_object->get("ATTRIBUTES") ne "nil") {
				foreach my $attribute_key($xml_object->get("ATTRIBUTES")->get("ALL_KEYS")) {
					my $attribute_value = $xml_object->get("ATTRIBUTES")->get("BY_KEY", $attribute_key);
					$retVal->set($attribute_key, $attribute_value);
				}
			}
		}
		elsif($xml_object->get("CLASS") eq "XMLContainer") {
			$retVal = SuperObject->new($logger);
			foreach my $xml_element($xml_object->toarray()){
				my $key = uc($xml_element->get("NAME"));
				my $value = $self->parse_object($xml_element);
				if($key =~ /.*?_DESCRIPTOR/ && $key ne "TYPED_DESCRIPTOR" && $key ne "STRING_DESCRIPTOR") {
					my $doceid = $value->get($key)->get("DOCEID");
					my ($keyframeid, $start, $end);
					if($key eq "TEXT_DESCRIPTOR") {
						$start = $value->get($key)->get("START");
						$end = $value->get($key)->get("END");
					}
					elsif($key eq "IMAGE_DESCRIPTOR") {
						$start = $value->get($key)->get("TOPLEFT");
						$end = $value->get($key)->get("BOTTOMRIGHT");
					}
					elsif($key eq "VIDEO_DESCRIPTOR") {
						$keyframeid = $value->get($key)->get("KEYFRAMEID");
						$start = $value->get($key)->get("TOPLEFT");
						$end = $value->get($key)->get("BOTTOMRIGHT");
					}
					if($key eq "AUDIO_DESCRIPTOR") {
						$start = $value->get($key)->get("START");
						$end = $value->get($key)->get("END");
					}
					else{
						$logger->record_problem("INVALID_JUSTIFICATION_TYPE", $key, $xml_object->get("WHERE"));
					}
					$value = NonStringDescriptor->new($logger, $key, $doceid, $keyframeid, $start, $end);
					$key = "DESCRIPTOR";
				}
				elsif($key eq "STRING_DESCRIPTOR") {
					$value = StringDescriptor->new($logger, $value->get($key));
					$key = "DESCRIPTOR";
				}
				$value = $value->get($key) if($key eq "TYPED_DESCRIPTOR");
				$retVal->set($key, $value);
			}
		}
	}
	$retVal;
}

# Determine if the response is valid:
##  (1). Is the queryid valid?
##  (2). Is the enttype matching?
##  (3). Depending on the scope see if the justifications come from the right set of documents
##  (4). The response is not valid if none of the justifications is valid
sub is_valid {
	my ($self) = @_;
	my $scope = $self->get("SCOPE");
	my $docid_mappings = $self->get("DOCID_MAPPINGS");
	my $query_id = $self->get("QUERYID");
	my $query = $self->get("QUERIES")->get("QUERY", $query_id);
	my $is_valid = 1;
	my $where = $self->get("XML_OBJECT")->get("WHERE");
	my $query_enttype = "unavailable";
	if($query) {
		$query_enttype = $query->get("ENTTYPE");
	}
	else {
		# Is the queryid valid?
		$self->get("LOGGER")->record_problem("UNKNOWN_QUERYID", $query_id, $where);
		$is_valid = 0;
	}
	my $i = 0;
	my %docids;
	my $num_valid_justifications = 0;
	foreach my $justification($self->get("JUSTIFICATIONS")->toarray()) {
		$i++;
		# Validate the justification span and confidence
		if ($justification->is_valid($docid_mappings, $scope)) {
			$num_valid_justifications++;
		}
		else {
			# Simply ignore the $justification
			# No need to ignore the entire object
			$justification->get("XML_OBJECT")->set("IGNORE", 1);
		}
		# Check if the enttype matches to that of the query
		if($query && $justification->get("ENTTYPE") ne $query_enttype) {
			$self->get("LOGGER")->record_problem("UNEXPECTED_ENTTYPE", $justification->get("ENTTYPE"), $query_enttype, $where);
			$is_valid = 0;
		}
		# Valiate documents used
		if($scope ne "anywhere") {
			# DOCID should be known to us
			my $doceid = $justification->get("DOCEID");
			if($docid_mappings->get("DOCUMENTELEMENTS")->exists($doceid)) {
				my $docelement = $docid_mappings->get("DOCUMENTELEMENTS")->get("BY_KEY", $doceid);
				my @docids = map {$_->get("DOCUMENTID")} $docelement->get("DOCUMENTS")->toarray();
				foreach my $docid(@docids) {
					$docids{$docid}++;
				}
			}
			else {
				$self->get("LOGGER")->record_problem("UNKNOWN_DOCUMENT_ELEMENT", $doceid, $where);
				$is_valid = 0;
			}
		}
		if($scope eq "withindoc") {
			my $response_docid = $self->get("RESPONSE_DOCID_FROM_FILENAME");
			my @justifiying_docs;
			foreach my $docid(keys %docids) {
				push(@justifiying_docs, $docid) if($docids{$docid} == $i);
			}
			unless(scalar grep {$_ eq $response_docid} @justifiying_docs) {
				$is_valid = 0;
				my $justifying_docs_string = join(",", @justifiying_docs);
				$self->get("LOGGER")->record_problem("UNEXPECTED_JUSTIFICATION_SOURCE", $justifying_docs_string, $response_docid, $where);
			}
		}
	}
	$is_valid = 0 unless $num_valid_justifications;
	$is_valid;
}

sub get_RESPONSE_FILENAME_PREFIX {
	my ($self) = @_;
	my $xml_file = $self->get("XML_FILENAME");
	$xml_file =~ /(^.*\/)+(.*?\..*?_responses.xml)/;
	my ($path, $filename) = ($1, $2);
	my ($prefix) = $filename =~ /^(.*?)\..*?_responses.xml/;
	$prefix;	
}

sub get_SYSTEM_TYPE {
	my ($self) = @_;
	my $prefix = $self->get("RESPONSE_FILENAME_PREFIX");
	my $system_type = "TA1";
	$system_type = "TA2" if $prefix eq "TA2";
	$system_type;
}

sub get_RESPONSE_DOCID_FROM_FILENAME {
	my ($self) = @_;
	my $response_docid = $self->get("RESPONSE_FILENAME_PREFIX");
	$response_docid = undef if $response_docid eq "TA2";
	$response_docid;
}

sub get_SCOPE {
	my ($self) = @_;
	my $docid_mappings = $self->get("DOCID_MAPPINGS");
	my $system_type = $self->get("SYSTEM_TYPE");
	my $response_docid = $self->get("RESPONSE_DOCID_FROM_FILENAME");
	my $scope = "anywhere";
	if($system_type eq "TA2") {
		$scope = "withincorpus";
	}
	elsif($response_docid) {
		$scope = "withindoc"
			if $docid_mappings->get("DOCUMENTS")->exists($response_docid);
	}
	$self->get("LOGGER")->NIST_die("Improper filename caused unexpected value for scope: $scope")
		if $scope eq "anywhere";
	$scope;
}

sub tostring {
	my ($self, $indent) = @_;
	$self->get("XML_OBJECT")->tostring($indent);
}

#####################################################################################
# ZeroHopResponse
#####################################################################################

package ZeroHopResponse;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $xml_object, $xml_filename, $queries, $docid_mappings) = @_;
  my $self = {
    CLASS => 'ZeroHopResponse',
    XML_FILENAME => $xml_filename,
    XML_OBJECT => $xml_object,
    DOCID_MAPPINGS => $docid_mappings,
    QUERIES => $queries,
    QUERYID => undef,
    JUSTIFICATIONS => undef,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load();
  $self;
}

sub load {
	my ($self) = @_;
	my $logger = $self->get("LOGGER");
	my $query_id = $self->get("XML_OBJECT")->get("ATTRIBUTES")->get("BY_KEY", "QUERY_ID");
	$self->set("QUERYID", $query_id);
	my $system_nodeid = $self->get("XML_OBJECT")->get("CHILD", "system_nodeid")->get("ELEMENT");
	$self->set("SYSTEM_NODEID", $system_nodeid);
	my $justifications = Container->new($logger, "Justification");
	my $i = 0;
	foreach my $justification_xml_object($self->get("XML_OBJECT")->get("ELEMENT")->toarray()){
		next if $justification_xml_object->get("NAME") eq "system_nodeid";
		$i++;
		my $doceid = $justification_xml_object->get("CHILD", "doceid")->get("ELEMENT");
		my $justification_type = uc $justification_xml_object->get("NAME");
		my $where = $justification_xml_object->get("WHERE");
		my $confidence = $justification_xml_object->get("CHILD", "confidence")->get("ELEMENT");
		my ($keyframeid, $start, $end, $enttype);
		if($justification_xml_object->get("NAME") eq "text_justification") {
			$start = $justification_xml_object->get("CHILD", "start")->get("ELEMENT");
			$end = $justification_xml_object->get("CHILD", "end")->get("ELEMENT");
		}
		elsif($justification_xml_object->get("NAME") eq "video_justification") {
			$keyframeid = $justification_xml_object->get("CHILD", "keyframeid")->get("ELEMENT");
			$start = $justification_xml_object->get("CHILD", "topleft")->get("ELEMENT");
			$end = $justification_xml_object->get("CHILD", "bottomright")->get("ELEMENT");
		}
		elsif($justification_xml_object->get("NAME") eq "image_justification") {
			$start = $justification_xml_object->get("CHILD", "topleft")->get("ELEMENT");
			$end = $justification_xml_object->get("CHILD", "bottomright")->get("ELEMENT");
		}
		elsif($justification_xml_object->get("NAME") eq "audio_justification") {
			$start = $justification_xml_object->get("CHILD", "start")->get("ELEMENT");
			$end = $justification_xml_object->get("CHILD", "end")->get("ELEMENT");
		}
		my $justification = Justification->new($logger, $justification_type, $doceid, $keyframeid, $start, $end, $enttype, $confidence, $justification_xml_object, $where);
		$justifications->add($justification, $i);
	}
	$self->set("JUSTIFICATIONS", $justifications);
}

sub parse_object {
	my ($self, $xml_object) = @_;
	my $logger = $self->get("LOGGER");
	my $retVal;
	if($xml_object->get("CLASS") eq "XMLElement" && !ref $xml_object->get("ELEMENT")) {
		# base-case of recursive function
		my $key = uc($xml_object->get("NAME"));
		my $value = $xml_object->get("ELEMENT");
		if($xml_object->get("ATTRIBUTES") ne "nil") {
			$retVal = SuperObject->new($logger);
			$retVal->set($key, $value);
			foreach my $attribute_key($xml_object->get("ATTRIBUTES")->get("ALL_KEYS")) {
				my $attribute_value = $xml_object->get("ATTRIBUTES")->get("BY_KEY", $attribute_key);
				$retVal->set($attribute_key, $attribute_value);
			}
		}
		else {
			$retVal = $value;
		}
	}
	else {
		if($xml_object->get("CLASS") eq "XMLElement") {
			my $key = uc($xml_object->get("NAME"));
			my $value = $self->parse_object($xml_object->get("ELEMENT"));
			$retVal = SuperObject->new($logger);
			$retVal->set($key, $value);
			if($xml_object->get("ATTRIBUTES") ne "nil") {
				foreach my $attribute_key($xml_object->get("ATTRIBUTES")->get("ALL_KEYS")) {
					my $attribute_value = $xml_object->get("ATTRIBUTES")->get("BY_KEY", $attribute_key);
					$retVal->set($attribute_key, $attribute_value);
				}
			}
		}
		elsif($xml_object->get("CLASS") eq "XMLContainer") {
			$retVal = SuperObject->new($logger);
			foreach my $xml_element($xml_object->toarray()){
				my $key = uc($xml_element->get("NAME"));
				my $value = $self->parse_object($xml_element);
				if($key =~ /.*?_DESCRIPTOR/ && $key ne "TYPED_DESCRIPTOR" && $key ne "STRING_DESCRIPTOR") {
					my $doceid = $value->get($key)->get("DOCEID");
					my ($keyframeid, $start, $end);
					if($key eq "TEXT_DESCRIPTOR") {
						$start = $value->get($key)->get("START");
						$end = $value->get($key)->get("END");
					}
					elsif($key eq "IMAGE_DESCRIPTOR") {
						$start = $value->get($key)->get("TOPLEFT");
						$end = $value->get($key)->get("BOTTOMRIGHT");
					}
					elsif($key eq "VIDEO_DESCRIPTOR") {
						$keyframeid = $value->get($key)->get("KEYFRAMEID");
						$start = $value->get($key)->get("TOPLEFT");
						$end = $value->get($key)->get("BOTTOMRIGHT");
					}
					if($key eq "AUDIO_DESCRIPTOR") {
						$start = $value->get($key)->get("START");
						$end = $value->get($key)->get("END");
					}
					else{
						# TODO: throw exception
					}
					$value = NonStringDescriptor->new($logger, $key, $doceid, $keyframeid, $start, $end);
					$key = "DESCRIPTOR";
				}
				elsif($key eq "STRING_DESCRIPTOR") {
					$value = StringDescriptor->new($logger, $value->get($key));
					$key = "DESCRIPTOR";
				}
				$value = $value->get($key) if($key eq "TYPED_DESCRIPTOR");
				$retVal->set($key, $value);
			}
		}
	}
	$retVal;
}

# Determine if the response is valid:
##  (1). Is the queryid valid?
##  (2). Is the enttype matching?
##  (3). Depending on the scope see if the justifications come from the right set of documents
##  (4). The response is not valid if none of the justifications is valid
sub is_valid {
	my ($self) = @_;
	my $scope = $self->get("SCOPE");
	my $docid_mappings = $self->get("DOCID_MAPPINGS");
	my $query_id = $self->get("QUERYID");
	my $query = $self->get("QUERIES")->get("QUERY", $query_id);
	my $is_valid = 1;
	my $where = $self->get("XML_OBJECT")->get("WHERE");
	unless($query) {
		# Is the queryid valid?
		$self->get("LOGGER")->record_problem("UNKNOWN_QUERYID", $query_id, $where);
		$is_valid = 0;
	}
	my $i = 0;
	my %docids;
	my $num_valid_justifications = 0;
	foreach my $justification($self->get("JUSTIFICATIONS")->toarray()) {
		$i++;
		# Validate the justification span and confidence
		if ($justification->is_valid($docid_mappings, $scope)) {
			$num_valid_justifications++;
		}
		else{
			# Simply ignore the $justification
			# No need to ignore the entire object
			$justification->get("XML_OBJECT")->set("IGNORE", 1);
		}
		# Valiate documents used
		if($scope ne "anywhere") {
			# DOCID should be known to us
			my $doceid = $justification->get("DOCEID");
			if($docid_mappings->get("DOCUMENTELEMENTS")->exists($doceid)) {
				my $docelement = $docid_mappings->get("DOCUMENTELEMENTS")->get("BY_KEY", $doceid);
				my @docids = map {$_->get("DOCUMENTID")} $docelement->get("DOCUMENTS")->toarray();
				foreach my $docid(@docids) {
					$docids{$docid}++;
				}
			}
			else {
				$self->get("LOGGER")->record_problem("UNKNOWN_DOCUMENT_ELEMENT", $doceid, $where);
				$is_valid = 0;
			}
		}
		if($scope eq "withindoc") {
			my $response_docid = $self->get("RESPONSE_DOCID_FROM_FILENAME");
			my @justifiying_docs;
			foreach my $docid(keys %docids) {
				push(@justifiying_docs, $docid) if($docids{$docid} == $i);
			}
			unless(scalar grep {$_ eq $response_docid} @justifiying_docs) {
				$is_valid = 0;
				my $justifying_docs_string = join(",", @justifiying_docs);
				$self->get("LOGGER")->record_problem("UNEXPECTED_JUSTIFICATION_SOURCE", $justifying_docs_string, $response_docid, $where);
			}
		}
	}
	$is_valid = 0 unless $num_valid_justifications;
	$is_valid;
}

sub get_RESPONSE_FILENAME_PREFIX {
	my ($self) = @_;
	my $xml_file = $self->get("XML_FILENAME");
	$xml_file =~ /(^.*\/)+(.*?\..*?_responses.xml)/;
	my ($path, $filename) = ($1, $2);
	my ($prefix) = $filename =~ /^(.*?)\..*?_responses.xml/;
	$prefix;	
}

sub get_SYSTEM_TYPE {
	my ($self) = @_;
	my $prefix = $self->get("RESPONSE_FILENAME_PREFIX");
	my $system_type = "TA1";
	$system_type = "TA2" if $prefix eq "TA2";
	$system_type;
}

sub get_RESPONSE_DOCID_FROM_FILENAME {
	my ($self) = @_;
	my $response_docid = $self->get("RESPONSE_FILENAME_PREFIX");
	$response_docid = undef if $response_docid eq "TA2";
	$response_docid;
}

sub get_SCOPE {
	my ($self) = @_;
	my $docid_mappings = $self->get("DOCID_MAPPINGS");
	my $system_type = $self->get("SYSTEM_TYPE");
	my $response_docid = $self->get("RESPONSE_DOCID_FROM_FILENAME");
	my $scope = "anywhere";
	if($system_type eq "TA2") {
		$scope = "withincorpus";
	}
	elsif($response_docid) {
		$scope = "withindoc"
			if $docid_mappings->get("DOCUMENTS")->exists($response_docid);
	}
	$self->get("LOGGER")->NIST_die("Improper filename caused unexpected value for scope: $scope")
		if $scope eq "anywhere";
	$scope;
}

sub tostring {
	my ($self, $indent) = @_;
	$self->get("XML_OBJECT")->tostring($indent);
}

#####################################################################################
# GraphResponse
#####################################################################################

package GraphResponse;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $xml_object, $xml_filename, $queries, $docid_mappings) = @_;
  my $self = {
    CLASS => 'GraphResponse',
    XML_FILENAME => $xml_filename,
    XML_OBJECT => $xml_object,
    DOCID_MAPPINGS => $docid_mappings,
    QUERIES => $queries,
    QUERYID => undef,
    EDGES => undef,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load();
  $self;
}

sub load {
	my ($self) = @_;
	my $logger = $self->get("LOGGER");
	my $query_id = $self->get("XML_OBJECT")->get("ATTRIBUTES")->get("BY_KEY", "id");
	$self->set("QUERYID", $query_id);
	my $edges = Container->new($logger);
	foreach my $edge_xml_object($self->get("XML_OBJECT")->get("CHILD", "response")->get("ELEMENT")->toarray()){
		my $edge = SuperObject->new($logger);
		my $edge_num = $edge_xml_object->get("ATTRIBUTES")->get("BY_KEY", "id");
		my $justifications = Container->new($logger);
		my $justification_num = 0;
		foreach my $justification_xml_object($edge_xml_object->get("ELEMENT")->get("ELEMENT")->toarray()) {
			$justification_num++;
			my $justification = SuperObject->new($logger);
			my $docid = $justification_xml_object->get("ATTRIBUTES")->get("BY_KEY", "docid");
			my $subjectjustification_xml_object = $justification_xml_object->get("CHILD", "subject_justification")->get("ELEMENT");
			my $subject_justification = $self->get("NODE_JUSTIFICATION", $subjectjustification_xml_object);
			my $objectjustification_xml_object = $justification_xml_object->get("CHILD", "object_justification")->get("ELEMENT");
			my $object_justification = $self->get("NODE_JUSTIFICATION", $objectjustification_xml_object);
			my $edgejustification_xml_object = $justification_xml_object->get("CHILD", "edge_justification")->get("ELEMENT");
			my $edge_justification = $self->get("EDGE_JUSTIFICATION", $edgejustification_xml_object);
			$justification->set("DOCID", $docid);
			$justification->set("SUBJECT_JUSTIFICATION", $subject_justification);
			$justification->set("OBJECT_JUSTIFICATION", $object_justification);
			$justification->set("EDGE_JUSTIFICATION", $edge_justification);
			$justification->set("XML_OBJECT", $justification_xml_object);
			$justifications->add($justification, $justification_num);
		}
		$edge->set("EDGE_NUM", $edge_num);
		$edge->set("JUSTIFICATIONS", $justifications);
		$edge->set("XML_OBJECT", $edge_xml_object);
		$edges->add($edge, $edge_num);
	}
	$self->set("EDGES", $edges);
}

sub parse_object {
	my ($self, $xml_object) = @_;
	my $logger = $self->get("LOGGER");
	my $retVal;
	if($xml_object->get("CLASS") eq "XMLElement" && !ref $xml_object->get("ELEMENT")) {
		# base-case of recursive function
		my $key = uc($xml_object->get("NAME"));
		my $value = $xml_object->get("ELEMENT");
		if($xml_object->get("ATTRIBUTES") ne "nil") {
			$retVal = SuperObject->new($logger);
			$retVal->set($key, $value);
			foreach my $attribute_key($xml_object->get("ATTRIBUTES")->get("ALL_KEYS")) {
				my $attribute_value = $xml_object->get("ATTRIBUTES")->get("BY_KEY", $attribute_key);
				$retVal->set($attribute_key, $attribute_value);
			}
		}
		else {
			$retVal = $value;
		}
	}
	else {
		if($xml_object->get("CLASS") eq "XMLElement") {
			my $key = uc($xml_object->get("NAME"));
			my $value = $self->parse_object($xml_object->get("ELEMENT"));
			$retVal = SuperObject->new($logger);
			$retVal->set($key, $value);
			if($xml_object->get("ATTRIBUTES") ne "nil") {
				foreach my $attribute_key($xml_object->get("ATTRIBUTES")->get("ALL_KEYS")) {
					my $attribute_value = $xml_object->get("ATTRIBUTES")->get("BY_KEY", $attribute_key);
					$retVal->set($attribute_key, $attribute_value);
				}
			}
		}
		elsif($xml_object->get("CLASS") eq "XMLContainer") {
			$retVal = SuperObject->new($logger);
			foreach my $xml_element($xml_object->toarray()){
				my $key = uc($xml_element->get("NAME"));
				my $value = $self->parse_object($xml_element);
				if($key =~ /.*?_DESCRIPTOR/ && $key ne "TYPED_DESCRIPTOR" && $key ne "STRING_DESCRIPTOR") {
					my $doceid = $value->get($key)->get("DOCEID");
					my ($keyframeid, $start, $end);
					if($key eq "TEXT_DESCRIPTOR") {
						$start = $value->get($key)->get("START");
						$end = $value->get($key)->get("END");
					}
					elsif($key eq "IMAGE_DESCRIPTOR") {
						$start = $value->get($key)->get("TOPLEFT");
						$end = $value->get($key)->get("BOTTOMRIGHT");
					}
					elsif($key eq "VIDEO_DESCRIPTOR") {
						$keyframeid = $value->get($key)->get("KEYFRAMEID");
						$start = $value->get($key)->get("TOPLEFT");
						$end = $value->get($key)->get("BOTTOMRIGHT");
					}
					if($key eq "AUDIO_DESCRIPTOR") {
						$start = $value->get($key)->get("START");
						$end = $value->get($key)->get("END");
					}
					else{
						# TODO: throw exception
					}
					$value = NonStringDescriptor->new($logger, $key, $doceid, $keyframeid, $start, $end);
					$key = "DESCRIPTOR";
				}
				elsif($key eq "STRING_DESCRIPTOR") {
					$value = StringDescriptor->new($logger, $value->get($key));
					$key = "DESCRIPTOR";
				}
				$value = $value->get($key) if($key eq "TYPED_DESCRIPTOR");
				$retVal->set($key, $value);
			}
		}
	}
	$retVal;
}

sub is_valid {
	my ($self) = @_;
	my $scope = $self->get("SCOPE");
	my $docid_mappings = $self->get("DOCID_MAPPINGS");
	my $query_id = $self->get("QUERYID");
	my $query = $self->get("QUERIES")->get("QUERY", $query_id);
	my $is_valid = 1;
	my $where = $self->get("XML_OBJECT")->get("WHERE");
	my $max_edge_justifications = 2;
	unless($query) {
		# Is the queryid valid?
		$self->get("LOGGER")->record_problem("UNKNOWN_QUERYID", $query_id, $where);
		$is_valid = 0;
	}
	# Check validity of edges
	my $num_valid_response_edges = 0;
	my @valid_edges;
	foreach my $response_edge($self->get("EDGES")->toarray()) {
		my $edge_num = $response_edge->get("EDGE_NUM");
		my $is_valid_response_edge = 1;
		# Check if edge_num mataches one in query
		my ($query_edge, $query_edge_predicate);
		if($query && $query->get("EDGES")->exists($edge_num)) {
			$query_edge = $query->get("EDGES")->get("BY_KEY", $edge_num);
			$query_edge_predicate = $query_edge->get("PREDICATE");
		}
		else{
			$self->get("LOGGER")->record_problem("UNKNOWN_EDGEID", $edge_num, $query_id, $where);
			$response_edge->get("XML_OBJECT")->set("IGNORE", 1);
			$is_valid_response_edge = 0;
		}
		my $num_valid_justifications = 0;
		foreach my $justification($response_edge->get("JUSTIFICATIONS")->toarray()) {
			my $is_justification_valid = 1;
			my $docid = $justification->get("DOCID");
			$is_justification_valid = 0
				unless($self->check_within_doc_spans($docid_mappings, $docid, $justification, $scope, $where));
			my $subject_enttype = $justification->get("SUBJECT_JUSTIFICATION")->get("ENTTYPE");
			if($query_edge_predicate && $query_edge_predicate !~ /^$subject_enttype\_/) {
				my ($query_edge_enttype, $predicate) = split(/_/, $query_edge_predicate);
				$self->get("LOGGER")->record_problem("UNEXPECTED_SUBJECT_ENTTYPE", $subject_enttype, $query_edge_enttype, $query_id, $edge_num, $where);
				$is_justification_valid = 0;
			}
			if($scope ne "anywhere" && !$docid_mappings->get("DOCUMENTS")->exists($docid)) {
				$self->get("LOGGER")->record_problem("UNKNOWN_DOCUMENT", $docid, $where);
				$is_justification_valid = 0;
			}
			$is_justification_valid = 0
				unless $justification->get("SUBJECT_JUSTIFICATION")->get("SPAN")->is_valid($docid_mappings, $scope);
			$is_justification_valid = 0
				unless $justification->get("OBJECT_JUSTIFICATION")->get("SPAN")->is_valid($docid_mappings, $scope);
			my @edge_justification_spans = $justification->get("EDGE_JUSTIFICATION")->get("SPANS")->toarray();
			my $num_edge_justification_spans = scalar @edge_justification_spans;
			my $num_valid_edge_justification_spans = 0;
			if($num_edge_justification_spans > $max_edge_justifications) {
				$self->get("LOGGER")->record_problem("EXTRA_EDGE_JUSTIFICATIONS", $max_edge_justifications, $num_edge_justification_spans, $where);
			}
			foreach my $edge_justification_span(@edge_justification_spans) {
				if($edge_justification_span->is_valid($docid_mappings, $scope)) {
					$num_valid_edge_justification_spans++;
					$edge_justification_span->get("XML_OBJECT")->set("IGNORE", 1)
						if($num_valid_edge_justification_spans);
				}
				else{
					$edge_justification_span->get("XML_OBJECT")->set("IGNORE", 1);
				}
			}
			$num_valid_justifications++ if($is_justification_valid);
			$justification->get("XML_OBJECT")->set("IGNORE", 1) unless $is_justification_valid;
		}
		unless($num_valid_justifications) {
			$response_edge->get("XML_OBJECT")->set("IGNORE", 1);
			$is_valid_response_edge = 0;
		}
		if ($is_valid_response_edge) {
			$num_valid_response_edges++;
			push(@valid_edges, $edge_num);
		}
	}
	# Check if the valid edges are all connected
	my %edges;
	my %nodes;
	foreach my $edge_num(@valid_edges) {
		if($query && $query->get("EDGES")->exists($edge_num)) {
			my $query_edge = $query->get("EDGES")->get("BY_KEY", $edge_num);
			$edges{$edge_num}{$query_edge->get("SUBJECT")} = 1;
			$edges{$edge_num}{$query_edge->get("OBJECT")} = 1;
			$nodes{$query_edge->get("SUBJECT")}{$edge_num} = 1;
			$nodes{$query_edge->get("OBJECT")}{$edge_num} = 1;
		}
	}
	my %reachable_nodes;
	if(scalar keys %nodes) {
		my ($a_nodeid) = (keys %nodes); # arbitrady node
		%reachable_nodes = ($a_nodeid => 1);
		my $flag = 1; # keep going flag
		while($flag){
			my @new_nodes;
			foreach my $node_id(keys %reachable_nodes) {
				foreach my $edge_num(keys %{$nodes{$node_id}}) {
					foreach my $other_nodeid(keys %{$edges{$edge_num}}) {
						push(@new_nodes, $other_nodeid)
								unless $reachable_nodes{$other_nodeid};
					}
				}
			}
			if(@new_nodes){
				foreach my $new_nodeid(@new_nodes) {
					$reachable_nodes{$new_nodeid} = 1;
				}
			}
			else{
				$flag = 0;
			}
		}
	}
	my $num_all_valid_nodes = scalar keys %nodes;
	my $num_reachable_nodes = scalar keys %reachable_nodes;
	$self->get("LOGGER")->record_problem("DISCONNECTED_VALID_GRAPH", $where)
		if($num_reachable_nodes != $num_all_valid_nodes);

	$self->get("XML_OBJECT")->set("IGNORE", 1) unless $num_valid_response_edges;
	$num_valid_response_edges;
}


sub get_RESPONSE_FILENAME_PREFIX {
	my ($self) = @_;
	my $xml_file = $self->get("XML_FILENAME");
	$xml_file =~ /(^.*\/)+(.*?\..*?_responses.xml)/;
	my ($path, $filename) = ($1, $2);
	my ($prefix) = $filename =~ /^(.*?)\..*?_responses.xml/;
	$prefix;	
}

sub get_SYSTEM_TYPE {
	my ($self) = @_;
	my $prefix = $self->get("RESPONSE_FILENAME_PREFIX");
	my $system_type = "TA1";
	$system_type = "TA2" if $prefix eq "TA2";
	$system_type;
}

sub get_RESPONSE_DOCID_FROM_FILENAME {
	my ($self) = @_;
	my $response_docid = $self->get("RESPONSE_FILENAME_PREFIX");
	$response_docid = undef if $response_docid eq "TA2";
	$response_docid;
}

sub get_SCOPE {
	my ($self) = @_;
	my $docid_mappings = $self->get("DOCID_MAPPINGS");
	my $system_type = $self->get("SYSTEM_TYPE");
	my $response_docid = $self->get("RESPONSE_DOCID_FROM_FILENAME");
	my $scope = "anywhere";
	if($system_type eq "TA2") {
		$scope = "withincorpus";
	}
	elsif($response_docid) {
		$scope = "withindoc"
			if $docid_mappings->get("DOCUMENTS")->exists($response_docid);
	}
	$self->get("LOGGER")->NIST_die("Improper filename caused unexpected value for scope: $scope")
		if $scope eq "anywhere";
	$scope;
}

sub get_NODE_JUSTIFICATION {
	my ($self, $xml_object) = @_;
	my $system_nodeid = $xml_object->get("CHILD", "system_nodeid")->get("ELEMENT");
	my $enttype = $xml_object->get("CHILD", "enttype")->get("ELEMENT");
	my $doceid = $xml_object->get("CHILD", "doceid")->get("ELEMENT");
	my $confidence = $xml_object->get("CHILD", "confidence")->get("ELEMENT");
	my ($keyframeid, $start, $end);
	my @span_xml_objects = grep {$_->get("NAME") =~ /^.*?span$/} $xml_object->toarray();
	# TODO: throw an error if there are more than one spans
	my $span_xml_object = $span_xml_objects[0];
	if($span_xml_object->get("NAME") eq "text_span") {
		$start = $span_xml_object->get("CHILD", "start")->get("ELEMENT");
		$end = $span_xml_object->get("CHILD", "end")->get("ELEMENT");
	}
	elsif($span_xml_object->get("NAME") eq "video_span") {
		$keyframeid = $span_xml_object->get("CHILD", "keyframeid")->get("ELEMENT");
		$start = $span_xml_object->get("CHILD", "topleft")->get("ELEMENT");
		$end = $span_xml_object->get("CHILD", "bottomright")->get("ELEMENT");
	}
	elsif($span_xml_object->get("NAME") eq "image_span") {
		$start = $span_xml_object->get("CHILD", "topleft")->get("ELEMENT");
		$end = $span_xml_object->get("CHILD", "bottomright")->get("ELEMENT");
	}
	elsif($span_xml_object->get("NAME") eq "audio_span") {
		$start = $span_xml_object->get("CHILD", "start")->get("ELEMENT");
		$end = $span_xml_object->get("CHILD", "end")->get("ELEMENT");
	}
	my $where = $span_xml_object->get("WHERE");
	my $justification_type = uc $span_xml_object->get("NAME");
	$justification_type =~ s/SPAN/JUSTIFICATION/;
	my $span = Justification->new($self->get("LOGGER"), $justification_type, $doceid, $keyframeid, $start, $end, $enttype, $confidence, $xml_object, $where);
	my $node_justification = SuperObject->new($self->get("LOGGER"));
	$node_justification->set("SYSTEM_NODEID", $system_nodeid);
	$node_justification->set("ENTTYPE", $enttype);
	$node_justification->set("SPAN", $span);
	$node_justification->set("CONFIDENCE", $confidence);
	$node_justification;
}

sub get_EDGE_JUSTIFICATION {
	my ($self, $xml_object) = @_;
	my $confidence = $xml_object->get("CHILD", "confidence")->get("ELEMENT");
	my ($keyframeid, $start, $end);
	my $spans = Container->new($self->get("LOGGER"));
	my @span_xml_objects = grep {$_->get("NAME") =~ /^.*?span$/} $xml_object->toarray();
	# TODO: throw an error/warning if there are more than two spans
	my $span_num = 0;
	foreach my $span_xml_object(@span_xml_objects) {
		$span_num++;
		my $doceid = $span_xml_object->get("CHILD", "doceid")->get("ELEMENT");
		my ($start, $end, $keyframeid, $enttype);
		if($span_xml_object->get("NAME") eq "text_span") {
			$start = $span_xml_object->get("CHILD", "start")->get("ELEMENT");
			$end = $span_xml_object->get("CHILD", "end")->get("ELEMENT");
		}
		elsif($span_xml_object->get("NAME") eq "video_span") {
			$keyframeid = $span_xml_object->get("CHILD", "keyframeid")->get("ELEMENT");
			$start = $span_xml_object->get("CHILD", "topleft")->get("ELEMENT");
			$end = $span_xml_object->get("CHILD", "bottomright")->get("ELEMENT");
		}
		elsif($span_xml_object->get("NAME") eq "image_span") {
			$start = $span_xml_object->get("CHILD", "topleft")->get("ELEMENT");
			$end = $span_xml_object->get("CHILD", "bottomright")->get("ELEMENT");
		}
		elsif($span_xml_object->get("NAME") eq "audio_span") {
			$start = $span_xml_object->get("CHILD", "start")->get("ELEMENT");
			$end = $span_xml_object->get("CHILD", "end")->get("ELEMENT");
		}
		my $where = $span_xml_object->get("WHERE");
		my $justification_type = uc $span_xml_object->get("NAME");
		$justification_type =~ s/SPAN/JUSTIFICATION/;
		my $span = Justification->new($self->get("LOGGER"), $justification_type, $doceid, $keyframeid, $start, $end, $enttype, $confidence, $xml_object, $where);
		$spans->add($span, $span_num);
	}
	my $edge_justification = SuperObject->new($self->get("LOGGER"));
	$edge_justification->set("CONFIDENCE", $confidence);
	$edge_justification->set("SPANS", $spans);
	$edge_justification;
}

sub check_within_doc_spans {
	my ($self, $docid_mappings, $docid, $justification, $scope, $where) = @_;
	my $is_valid = 1;
	my @spans = (
								$justification->get("SUBJECT_JUSTIFICATION")->get("SPAN"),
								$justification->get("OBJECT_JUSTIFICATION")->get("SPAN"),
								$justification->get("EDGE_JUSTIFICATION")->get("SPANS")->toarray(),
							);
	my %doceids = map {$_->get("DOCEID")=>1} @spans;
	foreach my $doceid(keys %doceids) {
		if($docid_mappings->get("DOCUMENTELEMENTS")->exists($doceid)) {
			my %docids =
				map {$_->get("DOCUMENTID")=>1}
				$docid_mappings->get("DOCUMENTELEMENTS")->get("BY_KEY", $doceid)->get("DOCUMENTS")->toarray();
			unless($docids{$docid}) {
				$self->get("LOGGER")->record_problem("ACROSS_DOCUMENT_JUSTIFICATION", $docid, $where);
				$is_valid = 0;
			}
		}
		elsif($scope ne "anywhere"){
			$self->get("LOGGER")->record_problem("UNKNOWN_DOCUMENT_ELEMENT", $doceid, $where);
		}
	}
	$is_valid;
}

sub tostring {
	my ($self, $indent) = @_;
	$self->get("XML_OBJECT")->tostring($indent);
}

#####################################################################################
# QuerySet
#####################################################################################

package QuerySet;

use parent -norequire, 'Super';

sub new {
	my ($class, $logger, $dtd_filename, $xml_filename) = @_;
	my $self = {
		CLASS => 'QuerySet',
		DTD_FILENAME => $dtd_filename,
		XML_FILENAME => $xml_filename,
		QUERIES => Container->new($logger, "Query"),
		LOGGER => $logger,
	};
	bless($self, $class);
	$self->load();
	$self;
}

sub load {
	my ($self) = @_;
	my $logger = $self->get("LOGGER");
	my $dtd_filename = $self->get("DTD_FILENAME");
	my $xml_filename = $self->get("XML_FILENAME");
	my $query_type = $dtd_filename;
	$query_type =~ s/^(.*?\/)+//g;
	$query_type =~ s/.dtd//;
	$self->set("QUERYTYPE", $query_type);
	my $xml_filehandler = XMLFileHandler->new($logger, $dtd_filename, $xml_filename);
	while(my $xml_query_object = $xml_filehandler->get("NEXT_OBJECT")) {
		my $query;
		$query = ClassQuery->new($logger, $xml_query_object) if($query_type eq "class_query");
		$query = ZeroHopQuery->new($logger, $xml_query_object) if($query_type eq "zerohop_query");
		$query = GraphQuery->new($logger, $xml_query_object) if($query_type eq "graph_query");
		$self->get("QUERIES")->add($query, $query->get("QUERYID"));
	}
}

sub get_QUERY {
	my ($self, $query_id) = @_;
	my $query;
	if($self->get("QUERIES")->exists($query_id)) {
		$query = $self->get("QUERIES")->get("BY_KEY", $query_id);
	}
	$query;
}

sub tostring {
	my ($self, $indent) = @_;
	my $retVal = "";
	foreach my $query($self->get("QUERIES")->toarray()) {
		$retVal .= $query->tostring($indent);
	}
	$retVal;
}

#####################################################################################
# ClassQuery
#####################################################################################

package ClassQuery;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $xml_object) = @_;
  my $self = {
    CLASS => 'ClassQuery',
    QUERYID => undef,
    QUERYTYPE => undef,
    ENTTYPE => undef,
    SPARQL => undef,
    XML_OBJECT => $xml_object,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load();
  $self;
}

sub load {
	my ($self) = @_;
	my $query_id = $self->get("XML_OBJECT")->get("ATTRIBUTES")->get("BY_KEY", "id");
	my $query_type = "class_query";
	$self->get("LOGGER")->record_problem("UNEXPECTED_QUERY_TYPE", $self->get("XML_OBJECT")->get("NAME"), $self->get("WHERE")) 
		if $self->get("XML_OBJECT")->get("NAME") ne $query_type;
	$self->set("QUERYID", $query_id);
	$self->set("QUERYTYPE", $query_type);
	$self->set("ENTTYPE", $self->get("XML_OBJECT")->get("CHILD", "enttype")->get("ELEMENT"));
	$self->set("SPARQL", $self->get("XML_OBJECT")->get("CHILD", "sparql")->get("ELEMENT"));
}

sub tostring {
	my ($self, $indent) = @_;
	$self->get("XML_OBJECT")->tostring($indent);
}

#####################################################################################
# ZeroHopQuery
#####################################################################################

package ZeroHopQuery;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $xml_object) = @_;
  my $self = {
    CLASS => 'ZeroHopQuery',
    XML_OBJECT => $xml_object,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load();
  $self;
}

sub load {
	my ($self) = @_;
	my $query_id = $self->get("XML_OBJECT")->get("ATTRIBUTES")->get("BY_KEY", "id");
	my $query_type = "zerohop_query";
	$self->get("LOGGER")->record_problem("UNEXPECTED_QUERY_TYPE", $self->get("XML_OBJECT")->get("NAME"), $self->get("WHERE")) 
		if $self->get("XML_OBJECT")->get("NAME") ne $query_type;
	$self->set("QUERYID", $query_id);
	$self->set("ENTRYPOINT", $self->parse_object($self->get("XML_OBJECT")->get("CHILD", "entrypoint")->get("ELEMENT")));
	$self->set("SPARQL", $self->get("XML_OBJECT")->get("CHILD", "sparql")->get("ELEMENT"));
}

sub parse_object {
	my ($self, $xml_object) = @_;
	my $logger = $self->get("LOGGER");
	my $retVal;
	if($xml_object->get("CLASS") eq "XMLElement" && !ref $xml_object->get("ELEMENT")) {
		# base-case of recursive function
		my $key = uc($xml_object->get("NAME"));
		my $value = $xml_object->get("ELEMENT");
		if($xml_object->get("ATTRIBUTES") ne "nil") {
			$retVal = SuperObject->new($logger);
			$retVal->set($key, $value);
			foreach my $attribute_key($xml_object->get("ATTRIBUTES")->get("ALL_KEYS")) {
				my $attribute_value = $xml_object->get("ATTRIBUTES")->get("BY_KEY", $attribute_key);
				$retVal->set($attribute_key, $attribute_value);
			}
		}
		else {
			$retVal = $value;
		}
	}
	else {
		if($xml_object->get("CLASS") eq "XMLElement") {
			my $key = uc($xml_object->get("NAME"));
			my $value = $self->parse_object($xml_object->get("ELEMENT"));
			$retVal = SuperObject->new($logger);
			$retVal->set($key, $value);
			if($self->get("ATTRIBUTES") ne "nil") {
				foreach my $attribute_key($self->get("ATTRIBUTES")->get("ALL_KEYS")) {
					my $attribute_value = $self->get("ATTRIBUTES")->get("BY_KEY", $attribute_key);
					$retVal->set($attribute_key, $attribute_value);
				}
			}
		}
		elsif($xml_object->get("CLASS") eq "XMLContainer") {
			$retVal = SuperObject->new($logger);
			foreach my $xml_element($xml_object->toarray()){
				my $key = uc($xml_element->get("NAME"));
				my $value = $self->parse_object($xml_element);
				if($key =~ /.*?_DESCRIPTOR/) {
					my $doceid = $value->get($key)->get("DOCEID");
					my ($keyframeid, $start, $end);
					if($key eq "TEXT_DESCRIPTOR") {
						$start = $value->get($key)->get("START");
						$end = $value->get($key)->get("END");
					}
					elsif($key eq "IMAGE_DESCRIPTOR") {
						$start = $value->get($key)->get("TOPLEFT");
						$end = $value->get($key)->get("BOTTOMRIGHT");
					}
					elsif($key eq "VIDEO_DESCRIPTOR") {
						$keyframeid = $value->get($key)->get("KEYFRAMEID");
						$start = $value->get($key)->get("TOPLEFT");
						$end = $value->get($key)->get("BOTTOMRIGHT");
					}
					if($key eq "AUDIO_DESCRIPTOR") {
						$start = $value->get($key)->get("START");
						$end = $value->get($key)->get("END");
					}
					else{
						# TODO: throw exception
					}
					$value = NonStringDescriptor->new($logger, $key, $doceid, $keyframeid, $start, $end);
					$key = "DESCRIPTOR";
				}
				$retVal->set($key, $value);
			}
		}
	}
	$retVal;
}

sub tostring {
	my ($self, $indent) = @_;
	$self->get("XML_OBJECT")->tostring($indent);
}

#####################################################################################
# GraphQuery
#####################################################################################

package GraphQuery;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $xml_object) = @_;
  my $self = {
    CLASS => 'GraphQuery',
    XML_OBJECT => $xml_object,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load();
  $self;
}

sub load {
	my ($self) = @_;
	my $query_id = $self->get("XML_OBJECT")->get("ATTRIBUTES")->get("BY_KEY", "id");
	my $query_type = "graph_query";
	$self->get("LOGGER")->record_problem("UNEXPECTED_QUERY_TYPE", $self->get("XML_OBJECT")->get("NAME"), $self->get("WHERE")) 
		if $self->get("XML_OBJECT")->get("NAME") ne $query_type;
	$self->set("QUERYID", $query_id);
	
	my $edges_xml_object = $self->get("XML_OBJECT")->get("CHILD", "edges");
	my $edges = Container->new($self->get("LOGGER"), "SuperObject");
	foreach my $edge_object($edges_xml_object->get("ELEMENT")->toarray()){
		my $parsed_object = $self->parse_object($edge_object);
		my $edge_num = $parsed_object->get("id");
		my $subject = $parsed_object->get("EDGE")->get("SUBJECT");
		my $predicate = $parsed_object->get("EDGE")->get("PREDICATE");
		my $object = $parsed_object->get("EDGE")->get("OBJECT");
		my $where = $self->get("XML_OBJECT")->get("WHERE");
		my $edge = Edge->new($self->get("LOGGER"), $edge_num, $subject, $predicate, $object, $where);
		$edges->add($edge, $edge_num);
	}
	$self->set("EDGES", $edges);

	my $entrypoints_xml_object = $self->get("XML_OBJECT")->get("CHILD", "entrypoints");
	my $entrypoints = Container->new($self->get("LOGGER"), "SuperObject");
	my $i = 0;
	foreach my $entrypoint($entrypoints_xml_object->get("ELEMENT")->toarray()){
		$i++;
		my $parsed_object = $self->parse_object($entrypoint);
		$entrypoints->add($parsed_object->get("ENTRYPOINT"), $i);
	}
	$self->set("ENTRYPOINTS", $entrypoints);
	$self->set("SPARQL", $self->get("XML_OBJECT")->get("CHILD", "sparql")->get("ELEMENT"));
}

sub parse_object {
	my ($self, $xml_object) = @_;
	my $logger = $self->get("LOGGER");
	my $retVal;
	if($xml_object->get("CLASS") eq "XMLElement" && !ref $xml_object->get("ELEMENT")) {
		# base-case of recursive function
		my $key = uc($xml_object->get("NAME"));
		my $value = $xml_object->get("ELEMENT");
		if($xml_object->get("ATTRIBUTES") ne "nil") {
			$retVal = SuperObject->new($logger);
			$retVal->set($key, $value);
			foreach my $attribute_key($xml_object->get("ATTRIBUTES")->get("ALL_KEYS")) {
				my $attribute_value = $xml_object->get("ATTRIBUTES")->get("BY_KEY", $attribute_key);
				$retVal->set($attribute_key, $attribute_value);
			}
		}
		else {
			$retVal = $value;
		}
	}
	else {
		if($xml_object->get("CLASS") eq "XMLElement") {
			my $key = uc($xml_object->get("NAME"));
			my $value = $self->parse_object($xml_object->get("ELEMENT"));
			$retVal = SuperObject->new($logger);
			$retVal->set($key, $value);
			if($xml_object->get("ATTRIBUTES") ne "nil") {
				foreach my $attribute_key($xml_object->get("ATTRIBUTES")->get("ALL_KEYS")) {
					my $attribute_value = $xml_object->get("ATTRIBUTES")->get("BY_KEY", $attribute_key);
					$retVal->set($attribute_key, $attribute_value);
				}
			}
		}
		elsif($xml_object->get("CLASS") eq "XMLContainer") {
			$retVal = SuperObject->new($logger);
			foreach my $xml_element($xml_object->toarray()){
				my $key = uc($xml_element->get("NAME"));
				my $value = $self->parse_object($xml_element);
				if($key =~ /.*?_DESCRIPTOR/ && $key ne "TYPED_DESCRIPTOR" && $key ne "STRING_DESCRIPTOR") {
					my $doceid = $value->get($key)->get("DOCEID");
					my ($keyframeid, $start, $end);
					if($key eq "TEXT_DESCRIPTOR") {
						$start = $value->get($key)->get("START");
						$end = $value->get($key)->get("END");
					}
					elsif($key eq "IMAGE_DESCRIPTOR") {
						$start = $value->get($key)->get("TOPLEFT");
						$end = $value->get($key)->get("BOTTOMRIGHT");
					}
					elsif($key eq "VIDEO_DESCRIPTOR") {
						$keyframeid = $value->get($key)->get("KEYFRAMEID");
						$start = $value->get($key)->get("TOPLEFT");
						$end = $value->get($key)->get("BOTTOMRIGHT");
					}
					if($key eq "AUDIO_DESCRIPTOR") {
						$start = $value->get($key)->get("START");
						$end = $value->get($key)->get("END");
					}
					else{
						# TODO: throw exception
					}
					$value = NonStringDescriptor->new($logger, $key, $doceid, $keyframeid, $start, $end);
					$key = "DESCRIPTOR";
				}
				elsif($key eq "STRING_DESCRIPTOR") {
					$value = StringDescriptor->new($logger, $value->get($key));
					$key = "DESCRIPTOR";
				}
				$value = $value->get($key) if($key eq "TYPED_DESCRIPTOR");
				$retVal->set($key, $value);
			}
		}
	}
	$retVal;
}

sub tostring {
	my ($self, $indent) = @_;
	$self->get("XML_OBJECT")->tostring($indent);
}

#####################################################################################
# Edge
#####################################################################################

package Edge;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $edge_num, $subject_id, $predicate, $object_id, $where) = @_;
  my $self = {
    CLASS => 'Edge',
    EDGENUM => $edge_num,
    SUBJECT => $subject_id,
    PREDICATE => $predicate,
    OBJECT => $object_id,
    WHERE => $where,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

#####################################################################################
# Justification
#####################################################################################

package Justification;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $justification_type, $doceid, $keyframeid, $start, $end, 
  		$enttype, $confidence, $xml_object, $where) = @_;
  my $self = {
    CLASS => 'Justification',
    TYPE => $justification_type,
    DOCEID => $doceid,
    KEYFRAMEID => $keyframeid,
    START => $start,
    END => $end,
    ENTTYPE => $enttype,
    CONFIDENCE => $confidence,
    XML_OBJECT => $xml_object,
    WHERE => $where,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub is_valid {
	my ($self, $docid_mappings, $scope) = @_;
	my $logger = $self->get("LOGGER");
	my $where = $self->get("WHERE");
	my $is_valid = 1;
	# Check if confidence is valid
	if(defined $self->get("CONFIDENCE")) {
		if($self->get("CONFIDENCE") < 0 || $self->get("CONFIDENCE") > 1) {
			$logger->record_problem("INVALID_CONFIDENCE", $self->get("CONFIDENCE"), $where);
			$is_valid = 0;
		}
	}
	my ($doceid, $keyframeid, $start, $end, $type)
				= map {$self->get($_)} qw(DOCEID KEYFRAMEID START END TYPE);
	my ($justification_modality) = $type =~ /^(.*?)_JUSTIFICATION$/;
	if($docid_mappings->get("DOCUMENTELEMENTS")->exists($doceid)) {
		my $document_element = 
			$docid_mappings->get("DOCUMENTELEMENTS")->get("BY_KEY", $doceid);
		my $de_type = $document_element->get("TYPE");
		my $de_modality = $document_element->get("MODALITY");
		$logger->record_problem("UNEXPECTED_JUSTIFICATION_MODALITY", $justification_modality, $doceid, $de_modality, $where)
			unless $de_modality eq $justification_modality;
	}
	if($type eq "TEXT_JUSTIFICATION" || $type eq "AUDIO_JUSTIFICATION") {
		if($start =~ /^-?\d+$/) {
			if ($start < 0) {
				$logger->record_problem("INVALID_START", $start, $type, $where);
				$is_valid = 0;
			}
		}
		else{
			$logger->record_problem("NONNUMERIC_START", $start, $where);
			$is_valid = 0;
		}
		if($end =~ /^-?\d+$/) {
			if ($end < 0) {
				$logger->record_problem("INVALID_END", $end, $type, $where);
				$is_valid = 0;
			}
		}
		else{
			$logger->record_problem("NONNUMERIC_END", $end, $where);
			$is_valid = 0;
		}
	}
	elsif($type eq "VIDEO_JUSTIFICATION" || $type eq "IMAGE_JUSTIFICATION") {
		unless ($start =~ /^\d+\,\d+$/) {
			$logger->record_problem("INVALID_START", $start, $type, $where);
			$is_valid = 0;
		}
		unless ($end =~ /^\d+\,\d+$/) {
			$logger->record_problem("INVALID_END", $end, $type, $where);
			$is_valid = 0;
		}
		if($type eq "VIDEO_JUSTIFICATION") {
			# For a video justification:
			#  (1) DOCEID should be the prefix of KEYFRAMEID
			#  (2) KEYFRAMEID should not end in an extension, e.g. .jpg
			if($keyframeid !~ /^$doceid\_\d+$/ || $keyframeid =~ /\..*?$/){
				$logger->record_problem("INVALID_KEYFRAMEID", $keyframeid, $where);
				$is_valid = 0;
			}
			# TODO: lookup keyframeid in the boundingbox file
		}
	}
	else {
		$logger->record_problem("INVALID_JUSTIFICATION_TYPE", $type, $where);
		$is_valid = 0;
	}
	$is_valid;
}

#####################################################################################
# StringDescriptor
#####################################################################################

package StringDescriptor;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $name_string) = @_;
  my $self = {
    CLASS => 'StringDescriptor',
    TYPE => "STRING_DESCRIPTOR",
    NAMESTRING => $name_string,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub tostring {
	my ($self) = @_;
	$self->get("NAMESTRING");
}

#####################################################################################
# NonStringDescriptor
#####################################################################################

package NonStringDescriptor;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $type, $doceid, $keyframeid, $start, $end) = @_;
  my $self = {
    CLASS => 'NonStringDescriptor',
    TYPE => $type,
    DOCEID => $doceid,
    KEYFRAMEID => $keyframeid,
    START => $start,
    END => $end,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub tostring {
	my ($self) = @_;
	my $doceid = $self->get("DOCEID");
	my $start = $self->get("START");
	my $end = $self->get("END");
	"$doceid:$start-$end";
}

#####################################################################################
# DocumentIDsMappings
#####################################################################################

package DocumentIDsMappings;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $filename) = @_;
  my $self = {
		CLASS => "DocumentIDsMappings",
		FILENAME => $filename,
		DOCUMENTS => Documents->new($logger),
    DOCUMENTELEMENTS => DocumentElements->new($logger),
    ENCODINGFORMAT_TO_MODALITY_MAPPINGS => EncodingFormatToModalityMappings->new($logger),
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load_data();
  $self;
}

sub load_data {
	my ($self) = @_;
	# Load the DocumentIDsMappingsFile
	my (%doceid_to_docid_mapping, %doceid_to_type_mapping);
	my $filename = $self->get("FILENAME");
	my $filehandler = FileHandler->new($self->get("LOGGER"), $filename);
	my $entries = $filehandler->get("ENTRIES");
	foreach my $entry($entries->toarray()) {
		my $doceid = $entry->get("doceid");
		my $docid = $entry->get("docid");
		my $detype = $entry->get("detype");
		$self->get("LOGGER")->record_problem("MISSING_ENCODING_FORMAT", $doceid, $entry->get("WHERE"))
			if $detype eq "nil";
		$doceid_to_docid_mapping{$doceid}{$docid} = 1;
		$doceid_to_type_mapping{$doceid} = $detype;
	}
	$filehandler->cleanup();

	foreach my $document_eid(sort keys %doceid_to_docid_mapping) {
		next if $document_eid eq "n/a";
		foreach my $document_id(sort keys %{$doceid_to_docid_mapping{$document_eid}}) {
			my $detype = $doceid_to_type_mapping{$document_eid};
			my $modality = $self->get("ENCODINGFORMAT_TO_MODALITY_MAPPINGS")->get("MODALITY_FROM_ENCODING_FORMAT", $detype);
			my $document = $self->get("DOCUMENTS")->get("BY_KEY", $document_id);
			$document->set("DOCUMENTID", $document_id);
			my $documentelement = $self->get("DOCUMENTELEMENTS")->get("BY_KEY", $document_eid);
			$documentelement->get("DOCUMENTS")->add($document, $document_id);
			$documentelement->set("DOCUMENTELEMENTID", $document_eid);
			$documentelement->set("TYPE", $detype);
			$documentelement->set("MODALITY", $modality);
			$document->add_document_element($documentelement);
		}
	}
}

#####################################################################################
# Documents
#####################################################################################

package Documents;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'Document');
  $self->{CLASS} = 'Documents';
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

#####################################################################################
# DocumentElements
#    contains 'DocumentElement' across documents
#####################################################################################

package DocumentElements;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'DocumentElement');
  $self->{CLASS} = 'DocumentElements';
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

#####################################################################################
# Document
#####################################################################################

package Document;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $document_id) = @_;
  my $self = {
    CLASS => 'Document',
    DOCUMENTID => $document_id,
    DOCUMENTELEMENTS => DocumentElements->new($logger),
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub add_document_element {
  my ($self, $document_element) = @_;
  $self->get("DOCUMENTELEMENTS")->add($document_element, $document_element->get("DOCUMENTELEMENTID"));
}

#####################################################################################
# DocumentElement
#####################################################################################

package DocumentElement;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = {
    CLASS => 'DocumentElement',
    DOCUMENTS => Documents->new($logger),
    DOCUMENTELEMENTID => undef,
    TYPE => undef,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

#####################################################################################
# EncodingFormatToModalityMappings
#####################################################################################

package EncodingFormatToModalityMappings;

use parent -norequire, 'Super';

my $encoding_format_to_modality_mapping = <<'END_ENCODING_MODALITY_MAPPING';

# Encoding Format      Modality
# ---------------      --------
gif                    image
jpg                    image
ltf                    text
mp3                    audio
mp4                    video
pdf                    pdf
png                    image
psm                    text
svg                    image
bmp                    image
vid                    video
img                    image

END_ENCODING_MODALITY_MAPPING

sub new {
	my ($class, $logger) = @_;
  my $self = {
    CLASS => 'EncodingFormatToModalityMappings',
    LOGGER => $logger,
  };
	bless($self, $class);
	$self->load_data();
	$self;
}

sub load_data {
	my ($self) = @_;
	chomp $encoding_format_to_modality_mapping;
  foreach (grep {/\S/} grep {!/^\S*#/} split(/\n/, $encoding_format_to_modality_mapping)) {
    s/^\s+//;
    my ($encoding_format, $modality) = split(/\s+/, $_, 2);
    $self->set($encoding_format, uc($modality));
  }
}

sub get_MODALITY_FROM_ENCODING_FORMAT {
	my ($self, $encoding_format) = @_;
	my $modality = $self->get($encoding_format);
	if($modality eq "nil") {
		$self->get("LOGGER")->record_problem("MISSING_MODALITY", $encoding_format, 
						{FILENAME => $self->get("FILENAME"), LINENUM => "n/a"});
	}
	$modality;
}

### BEGIN INCLUDE Utils
package main;
use JSON;

#####################################################################################
# UUIDs from UUID::Tiny
#####################################################################################

# The following UUID code is taken from UUID::Tiny, available on
# cpan.org. I have stripped out much of the functionality in that
# module, keeping only what's needed here. If there is a better way to
# deliver a cpan module within a single script, I'd love to know about
# it. I believe that this use conforms with the perl terms.

####################################
# From the UUID::Tiny documentation:
####################################

=head1 ACKNOWLEDGEMENTS

Kudos to ITO Nobuaki E<lt>banb@cpan.orgE<gt> for his UUID::Generator::PurePerl
module! My work is based on his code, and without it I would've been lost with
all those incomprehensible RFC texts and C codes ...

Thanks to Jesse Vincent (C<< <jesse at bestpractical.com> >>) for his feedback, tips and refactoring!

=head1 COPYRIGHT & LICENSE

Copyright 2009, 2010, 2013 Christian Augustin, all rights reserved.

This program is free software; you can redistribute it and/or modify it
under the same terms as Perl itself.

ITO Nobuaki has very graciously given me permission to take over copyright for
the portions of code that are copied from or resemble his work (see
rt.cpan.org #53642 L<https://rt.cpan.org/Public/Bug/Display.html?id=53642>).

=cut

use Digest::MD5;

our $IS_UUID_STRING = qr/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/is;
our $IS_UUID_HEX    = qr/^[0-9a-f]{32}$/is;
our $IS_UUID_Base64 = qr/^[+\/0-9A-Za-z]{22}(?:==)?$/s;

my $MD5_CALCULATOR = Digest::MD5->new();

use constant UUID_NIL => "\x00" x 16;
use constant UUID_V1 => 1; use constant UUID_TIME   => 1;
use constant UUID_V3 => 3; use constant UUID_MD5    => 3;
use constant UUID_V4 => 4; use constant UUID_RANDOM => 4;
use constant UUID_V5 => 5; use constant UUID_SHA1   => 5;

sub _create_v3_uuid {
    my $ns_uuid = shift;
    my $name    = shift;
    my $uuid    = '';

    # Create digest in UUID ...
    $MD5_CALCULATOR->reset();
    $MD5_CALCULATOR->add($ns_uuid);

    if ( ref($name) =~ m/^(?:GLOB|IO::)/ ) {
        $MD5_CALCULATOR->addfile($name);
    }
    elsif ( ref $name ) {
        Logger->new()->NIST_die('::create_uuid(): Name for v3 UUID'
            . ' has to be SCALAR, GLOB or IO object, not '
            . ref($name) .'!')
            ;
    }
    elsif ( defined $name ) {
    	# Use Encode to support Unicode.
        $MD5_CALCULATOR->add(Encode::encode_utf8($name));
    }
    else {
        Logger->new()->NIST_die('::create_uuid(): Name for v3 UUID is not defined!');
    }

    # Use only first 16 Bytes ...
    $uuid = substr( $MD5_CALCULATOR->digest(), 0, 16 );

    return _set_uuid_version( $uuid, 0x30 );
}

sub _set_uuid_version {
    my $uuid = shift;
    my $version = shift;
    substr $uuid, 6, 1, chr( ord( substr( $uuid, 6, 1 ) ) & 0x0f | $version );

    return $uuid;
}

sub create_uuid {
    use bytes;
    my ($v, $arg2, $arg3) = (shift || UUID_V1, shift, shift);
    my $uuid    = UUID_NIL;
    my $ns_uuid = string_to_uuid(defined $arg3 ? $arg2 : UUID_NIL);
    my $name    = defined $arg3 ? $arg3 : $arg2;

    ### Portions redacted from UUID::Tiny
    if ($v == UUID_V3 ) {
        $uuid = _create_v3_uuid($ns_uuid, $name);
    }
    else {
        Logger->new()->NIST_die("::create_uuid(): Invalid UUID version '$v'!");
    }

    # Set variant 2 in UUID ...
    substr $uuid, 8, 1, chr(ord(substr $uuid, 8, 1) & 0x3f | 0x80);

    return $uuid;
}

sub string_to_uuid {
    my $uuid = shift;

    use bytes;
    return $uuid if length $uuid == 16;
    return decode_base64($uuid) if ($uuid =~ m/$IS_UUID_Base64/);
    my $str = $uuid;
    $uuid =~ s/^(?:urn:)?(?:uuid:)?//io;
    $uuid =~ tr/-//d;
    return pack 'H*', $uuid if $uuid =~ m/$IS_UUID_HEX/;
    Logger->new()->NIST_die("::string_to_uuid(): '$str' is no UUID string!");
}

sub uuid_to_string {
    my $uuid = shift;
    use bytes;
    return $uuid
        if $uuid =~ m/$IS_UUID_STRING/;
    Logger->new()->NIST_die("::uuid_to_string(): Invalid UUID!")
        unless length $uuid == 16;
    return  join '-',
            map { unpack 'H*', $_ }
            map { substr $uuid, 0, $_, '' }
            ( 4, 2, 2, 2, 6 );
}

sub create_UUID_as_string {
    return uuid_to_string(create_uuid(@_));
}

#####################################################################################
# This is the end of the code taken from UUID::Tiny
#####################################################################################

my $json = JSON->new->allow_nonref->utf8;

sub generate_uuid_from_values {
  my ($queryid, $value, $provenance_string, $length) = @_;
  my $encoded_string = $json->encode("$queryid:$value:$provenance_string");
  $encoded_string =~ s/^"//;
  $encoded_string =~ s/"$//;
  &generate_uuid_from_string($encoded_string, $length);
}

sub generate_uuid_from_string {
  my ($string, $length) = @_;
  my $long_uuid = create_UUID_as_string(UUID_V3, $string);
  return substr($long_uuid, -$length, $length) if $length;
  $long_uuid;
}
### DO NOT INCLUDE
# sub uuid_generate {
#   my ($queryid, $value, $provenance_string) = @_;
#   my $encoded_string = $json->encode("$queryid:$value:$provenance_string");
#   $encoded_string =~ s/^"//;
#   $encoded_string =~ s/"$//;
# ### DO NOT INCLUDE
# # NOTE: this is the 2014 code, which special cased a query that had a funky character. I expect the patch is not backward compatible.  
# # # FIXME
# # my $glop = $value;
# # $glop =~ s/’/'/g;
# # #  create_UUID_as_string(UUID_V3, "$queryid:$value:$provenance_string");
# #  create_UUID_as_string(UUID_V3, "$queryid:$glop:$provenance_string");
# ### DO INCLUDE
#   # We're shortening the uuid for 2015
#   my $long_uuid = create_UUID_as_string(UUID_V3, $encoded_string);
#   substr($long_uuid, -12, 12);
# }

# sub short_uuid_generate {
#   my ($string) = @_;
#   my $encoded_string = $json->encode($string);
#   $encoded_string =~ s/^"//;
#   $encoded_string =~ s/"$//;
# ### DO NOT INCLUDE
# print STDERR "Original string = <<$string>>\n Encoded string = <<$encoded_string>>\n" unless $string eq $encoded_string;
# ### DO INCLUDE
#   my $long_uuid = create_UUID_as_string(UUID_V3, $encoded_string);
#   substr($long_uuid, -10, 10);
# }
### DO INCLUDE

sub min {
  my ($result, @values) = @_;
  foreach (@values) {
    $result = $_ if $_ < $result;
  }
  $result;
}

sub max {
  my ($result, @values) = @_;
  foreach (@values) {
    $result = $_ if $_ > $result;
  }
  $result;
}

sub remove_quotes {
  my ($string) = @_;
  if($string =~ /^"(.*)"$/) {
    return $1;
  }
  return $string;
}

# Pull DOCUMENTATION strings out of a table and format for the help screen
sub build_documentation {
  my ($structure, $sort_key) = @_;
  if (ref $structure eq 'HASH') {
    my $max_len = &max(map {length} keys %{$structure});
    "  " . join("\n  ", map {$_ . ": " . (' ' x ($max_len - length($_))) . $structure->{$_}{DESCRIPTION}}
		sort keys %{$structure}) . "\n";
  }
  elsif (ref $structure eq 'ARRAY') {
    $sort_key = 'TYPE' unless defined $sort_key;
    my $max_len = &max(map {length($_->{$sort_key})}  @{$structure});
    "  " . join("\n  ", map {$_->{$sort_key} . ": " . (' ' x ($max_len - length($_->{$sort_key}))) . $_->{DESCRIPTION}}
		sort {$a->{$sort_key} cmp $b->{$sort_key}} @{$structure}) . "\n";
  }
  else {
    "Internal error: Better call Saul.\n";
  }
}

sub dump_structure {
  my ($structure, $label, $indent, $history, $skip) = @_;
  if (ref $indent) {
    $skip = $indent;
    undef $indent;
  }
  my $outfile = *STDERR;
  $indent = 0 unless defined $indent;
  $history = {} unless defined $history;

  # Handle recursive structures
  if ($history->{$structure}) {
    print $outfile "  " x $indent, "$label: CIRCULAR\n";
    return;
  }

  my $type = ref $structure;
  unless ($type) {
    $structure = 'undef' unless defined $structure;
    print $outfile "  " x $indent, "$label: $structure\n";
    return;
  }
  if ($type eq 'ARRAY') {
    $history->{$structure}++;
    print $outfile "  " x $indent, "$label:\n";
    for (my $i = 0; $i < @{$structure}; $i++) {
      &dump_structure($structure->[$i], $i, $indent + 1, $history, $skip);
    }
  }
  elsif ($type eq 'CODE') {
    print $outfile "  " x $indent, "$label: CODE\n";
  }
  elsif ($type eq 'IO::File') {
    print $outfile "  " x $indent, "$label: IO::File\n";
  }
  else {
    $history->{$structure}++;
    print $outfile "  " x $indent, "$label:\n";
    my %done;
  outer:
    # You can add field names prior to the sort to order the fields in a desired way
    foreach my $key (sort keys %{$structure}) {
      if ($skip) {
	foreach my $skipname (@{$skip}) {
	  next outer if $key eq $skipname;
	}
      }
      next if $done{$key}++;
      # Skip undefs
      next unless defined $structure->{$key};
      &dump_structure($structure->{$key}, $key, $indent + 1, $history, $skip);
    }
  }
}

### END INCLUDE Utils

### BEGIN INCLUDE Switches

#####################################################################################
# This switch processing code written many years ago by James Mayfield
# and used here with permission. It really has nothing to do with
# TAC KBP; it's just a partial replacement for getopt that closely ties
# the documentation to the switch specification. The code may well be cheesy,
# so no peeking.
#####################################################################################

package SwitchProcessor;

sub _max {
    my $first = shift;
    my $second = shift;
    $first > $second ? $first : $second;
}

sub _quotify {
    my $string = shift;
    if (ref($string)) {
	join(", ", @{$string});
    }
    else {
	(!$string || $string =~ /\s/) ? "'$string'" : $string;
    }
}

sub _formatSubs {
    my $value = shift;
    my $switch = shift;
    my $formatted;
    if ($switch->{SUBVARS}) {
	$formatted = "";
	foreach my $subval (@{$value}) {
	    $formatted .= " " if $formatted;
	    $formatted .= _quotify($subval);
	}
    }
    # else if this is a constant switch, omit the vars [if they match?]
    else {
	$formatted = _quotify($value);
    }
    $formatted;
}

# Print an error message, display program usage, and exit unsuccessfully
sub _barf {
    my $self = shift;
    my $errstring = shift;
    open(my $handle, "|more") or Logger->new()->NIST_die("Couldn't even barf with message $errstring");
    print $handle "ERROR: $errstring\n";
    $self->showUsage($handle);
    close $handle;
    exit(-1);
}

# Create a new switch processor.  Arguments are the name of the
# program being run, and deneral documentation for the program
sub new {
    my $classname = shift;
    my $self = {};
    bless ($self, $classname);
    $self->{PROGNAME} = shift;
    $self->{PROGNAME} =~ s(^.*/)();
    $self->{DOCUMENTATION} = shift;
    $self->{POSTDOCUMENTATION} = shift;
    $self->{HASH} = {};
    $self->{PARAMS} = [];
    $self->{SWITCHWIDTH} = 0;
    $self->{PARAMWIDTH} = 0;
    $self->{SWITCHES} = {};
    $self->{VARSTOCHECK} = ();
    $self->{LEGALVARS} = {};
    $self->{PROCESS_INVOKED} = undef;
    $self;
}

# Fill a paragraph, with different leaders for first and subsequent lines
sub _fill {
    $_ = shift;
    my $leader1 = shift;
    my $leader2 = shift;
    my $width = shift;
    my $result = "";
    my $thisline = $leader1;
    my $spaceOK = undef;
    foreach my $word (split) {
	if (length($thisline) + length($word) + 1 <= $width) {
	    $thisline .= " " if ($spaceOK);
	    $spaceOK = "TRUE";
	    $thisline .= $word;
	}
	else {
			if(length($word) > $width) {
				my @chars = split("", $word);
				my $numsplits = int((scalar @chars/$width)) + 1;
				my $start  =  0;
				my $length =  @chars / $numsplits;

				foreach my $i (0 .. $numsplits-1)
				{
				    my $end = ($i == $numsplits-1) ? $#chars : $start + $length - 1;
				    my $splitword = join("", @chars[$start .. $end]);
				    $start += $length;
				    $result .= "$thisline\n";
				    $thisline = "$leader2$splitword";
				    $thisline .= "/" if $i < $numsplits-1;
				    $spaceOK = "TRUE";
				}
				
			}
			else {
		    $result .= "$thisline\n";
		    $thisline = "$leader2$word";
		    $spaceOK = "TRUE";
			}
	}
    }
    "$result$thisline\n";
}

# Show program usage
sub showUsage {
    my $self = shift;
    my $handle = shift;
    open($handle, "|more") unless defined $handle;
    print $handle _fill($self->{DOCUMENTATION}, "$self->{PROGNAME}:  ",
			" " x (length($self->{PROGNAME}) + 3), $terminalWidth);
    print $handle "\nUsage: $self->{PROGNAME}";
    print $handle " {-switch {-switch ...}}"
	if (keys(%{$self->{SWITCHES}}) > 0);
    # Count the number of optional parameters
    my $optcount = 0;
    # Print each parameter
    foreach my $param (@{$self->{PARAMS}}) {
	print $handle " ";
	print $handle "{" unless $param->{REQUIRED};
	print $handle $param->{NAME};
	$optcount++ if (!$param->{REQUIRED});
	print $handle "..." if $param->{ALLOTHERS};
    }
    # Close out the optional parameters
    print $handle "}" x $optcount;
    print $handle "\n\n";
    # Show details of each switch
    my $headerprinted = undef;
    foreach my $key (sort keys %{$self->{SWITCHES}}) {
	my $usage = "  $self->{SWITCHES}->{$key}->{USAGE}" .
	    " " x ($self->{SWITCHWIDTH} - length($self->{SWITCHES}->{$key}->{USAGE}) + 2);
	if (defined($self->{SWITCHES}->{$key}->{DOCUMENTATION})) {
	    print $handle "Legal switches are:\n"
		unless defined($headerprinted);
	    $headerprinted = "TRUE";
	    print $handle _fill($self->{SWITCHES}->{$key}->{DOCUMENTATION},
			$usage,
			" " x (length($usage) + 2),
			$terminalWidth);
	}
    }
    # Show details of each parameter
    if (@{$self->{PARAMS}} > 0) {
	print $handle "parameters are:\n";
	foreach my $param (@{$self->{PARAMS}}) {
	    my $usage = "  $param->{USAGE}" .
		" " x ($self->{PARAMWIDTH} - length($param->{USAGE}) + 2);
	    print $handle _fill($param->{DOCUMENTATION}, $usage, " " x (length($usage) + 2), $terminalWidth);
	}
    }
    print $handle "\n$self->{POSTDOCUMENTATION}\n" if $self->{POSTDOCUMENTATION};
}

# Retrieve all keys defined for this switch processor
sub keys {
    my $self = shift;
    keys %{$self->{HASH}};
}

# Add a switch that causes display of program usage
sub addHelpSwitch {
    my $self = shift;
    my ($shouldBeUndef, $filename, $line) = caller;
    my $switch = SP::_Switch->newHelp($filename, $line, @_);
    $self->_addSwitch($filename, $line, $switch);
}

# Add a switch that causes a given variable(s) to be assigned a given
# constant value(s)
sub addConstantSwitch {
    my $self = shift;
    my ($shouldBeUndef, $filename, $line) = caller;
    my $switch = SP::_Switch->newConstant($filename, $line, @_);
    $self->_addSwitch($filename, $line, $switch);
}

# Add a switch that assigns to a given variable(s) value(s) provided
# by the user on the command line
sub addVarSwitch {
    my $self = shift;
    my ($shouldBeUndef, $filename, $line) = caller;
    my $switch = SP::_Switch->newVar($filename, $line, @_);
    $self->_addSwitch($filename, $line, $switch);
}

# Add a switch that invokes a callback as soon as it is encountered on
# the command line.  The callback receives three arguments: the switch
# object (which is needed by the internal routines, but presumably may
# be ignored by user-defined functions), the switch processor, and all
# the remaining arguments on the command line after the switch (as the
# remainder of @_, not a reference).  If it returns, it must return
# the list of command-line arguments that remain after it has dealt
# with whichever ones it wants to.
sub addImmediateSwitch {
    my $self = shift;
    my ($shouldBeUndef, $filename, $line) = caller;
    my $switch = SP::_Switch->newImmediate($filename, $line, @_);
    $self->_addSwitch($filename, $line, $switch);
}

sub addMetaSwitch {
    my $self = shift;
    my ($shouldBeUndef, $filename, $line) = caller;
    my $switch = SP::_Switch->newMeta($filename, $line, @_);
    $self->_addSwitch($filename, $line, $switch);
}

# Add a new switch
sub _addSwitch {
    my $self = shift;
    my $filename = shift;
    my $line = shift;
    my $switch = shift;
    # Can't add switches after process() has been invoked
    Logger->new()->NIST_die("Attempt to add a switch after process() has been invoked, at $filename line $line\n")
	if ($self->{PROCESS_INVOKED});
    # Bind the switch object to its name
    $self->{SWITCHES}->{$switch->{NAME}} = $switch;
    # Remember how much space is required for the usage line
    $self->{SWITCHWIDTH} = _max($self->{SWITCHWIDTH}, length($switch->{USAGE}))
	if (defined($switch->{DOCUMENTATION}));
    # Make a note of the variable names that are legitimized by this switch
    $self->{LEGALVARS}->{$switch->{NAME}} = "TRUE";
}

# Add a new command-line parameter
sub addParam {
    my ($shouldBeUndef, $filename, $line) = caller;
    my $self = shift;
    # Can't add params after process() has been invoked
    Logger->new()->NIST_die("Attempt to add a param after process() has been invoked, at $filename line $line\n")
	if ($self->{PROCESS_INVOKED});
    # Create the parameter object
    my $param = SP::_Param->new($filename, $line, @_);
    # Remember how much space is required for the usage line
    $self->{PARAMWIDTH} = _max($self->{PARAMWIDTH}, length($param->{NAME}));
    # Check for a couple of potential problems with parameter ordering
    if (@{$self->{PARAMS}} > 0) {
	my $previous = ${$self->{PARAMS}}[$#{$self->{PARAMS}}];
        Logger->new()->NIST_die("Attempt to add param after an allOthers param, at $filename line $line\n")
	    if ($previous->{ALLOTHERS});
        Logger->new()->NIST_die("Attempt to add required param after optional param, at $filename line $line\n")
	    if ($param->{REQUIRED} && !$previous->{REQUIRED});
    }
    # Make a note of the variable names that are legitimized by this param
    $self->{LEGALVARS}->{$param->{NAME}} = "TRUE";
    # Add the parameter object to the list of parameters for this program
    push(@{$self->{PARAMS}}, $param);
}

# Set a switch processor variable to a given value
sub put {
    my $self = shift;
    my $key = shift;
    my $value = shift;
    my ($shouldBeUndef, $filename, $line) = caller;
    $self->_varNameCheck($filename, $line, $key, undef);
    my $switch = $self->{SWITCHES}->{$key};
    Logger->new()->NIST_die("Wrong number of values in second argument to put, at $filename line $line.\n")
	if ($switch->{SUBVARS} &&
	    (!ref($value) ||
	     scalar(@{$value}) != @{$switch->{SUBVARS}}));
    $self->{HASH}->{$key} = $value;
}

# Get the value of a switch processor variable
sub get {
    my $self = shift;
    my $key = shift;
    # Internally, we sometimes want to do a get before process() has
    # been invoked.  The secret second argument to get allows this.
    my $getBeforeProcess = shift;
    my ($shouldBeUndef, $filename, $line) = caller;
    Logger->new()->NIST_die("Get called before process, at $filename line $line\n")
	if (!$self->{PROCESS_INVOKED} && !$getBeforeProcess);
    # Check for var.subvar syntax
    $key =~ /([^.]*)\.*(.*)/;
    my $var = $1;
    my $subvar = $2;
    # Make sure this is a legitimate switch processor variable
    $self->_varNameCheck($filename, $line, $var, $subvar);
    my $value = $self->{HASH}->{$var};
    $subvar ? $value->[$self->_getSubvarIndex($var, $subvar)] : $value;
}

sub _getSubvarIndex {
    my $self = shift;
    my $var = shift;
    my $subvar = shift;
    my $switch = $self->{SWITCHES}->{$var};
    return(-1) unless $switch;
    return(-1) unless $switch->{SUBVARS};
    for (my $i = 0; $i < @{$switch->{SUBVARS}}; $i++) {
	return($i) if ${$switch->{SUBVARS}}[$i] eq $subvar;
    }
    -1;
}

# Check whether a given switch processor variable is legitimate
sub _varNameCheck {
    my $self = shift;
    my $filename = shift;
    my $line = shift;
    my $key = shift;
    my $subkey = shift;
    # If process() has already been invoked, check the variable name now...
    if ($self->{PROCESS_INVOKED}) {
	$self->_immediateVarNameCheck($filename, $line, $key, $subkey);
    }
    # ...Otherwise, remember the variable name and check it later
    else {
	push(@{$self->{VARSTOCHECK}}, [$filename, $line, $key, $subkey]);
    }
}

# Make sure this variable is legitimate
sub _immediateVarNameCheck {
    my $self = shift;
    my $filename = shift;
    my $line = shift;
    my $key = shift;
    my $subkey = shift;
    Logger->new()->NIST_die("No such SwitchProcessor variable: $key, at $filename line $line\n")
	unless $self->{LEGALVARS}->{$key};
    Logger->new()->NIST_die("No such SwitchProcessor subvariable: $key.$subkey, at $filename line $line\n")
	unless (!$subkey || $self->_getSubvarIndex($key, $subkey) >= 0);
}

# Add default values to switch and parameter documentation strings,
# where appropriate
sub _addDefaultsToDoc {
    my $self = shift;
    # Loop over all switches
    foreach my $switch (values %{$self->{SWITCHES}}) {
	if ($switch->{METAMAP}) {
	    $switch->{DOCUMENTATION} .= " (Equivalent to";
	    foreach my $var (sort CORE::keys %{$switch->{METAMAP}}) {
		my $rawval = $switch->{METAMAP}->{$var};
		my $val = SwitchProcessor::_formatSubs($rawval, $self->{SWITCHES}->{$var});
		$switch->{DOCUMENTATION} .= " -$var $val";
	    }
	    $switch->{DOCUMENTATION} .= ")";
	}
	# Default values aren't reported for constant switches
	if (!defined($switch->{CONSTANT})) {
	    my $default = $self->get($switch->{NAME}, "TRUE");
	    if (defined($default)) {
		$switch->{DOCUMENTATION} .= " (Default = " . _formatSubs($default, $switch) . ").";
	    }
	}
    }
    # Loop over all params
    foreach my $param (@{$self->{PARAMS}}) {
	my $default = $self->get($param->{NAME}, "TRUE");
	# Add default to documentation if the switch is optional and there
	# is a default value
	$param->{DOCUMENTATION} .= " (Default = " . _quotify($default) . ")."
	    if (!$param->{REQUIRED} && defined($default));
    }
}

# Process the command line
sub process {
    my $self = shift;
    # Add defaults to the documentation
    $self->_addDefaultsToDoc();
    # Remember that process() has been invoked
    $self->{PROCESS_INVOKED} = "TRUE";
    # Now that all switches have been defined, check all pending
    # variable names for legitimacy
    foreach (@{$self->{VARSTOCHECK}}) {
	# FIXME: Can't we just use @{$_} here?
	$self->_immediateVarNameCheck(${$_}[0], ${$_}[1], ${$_}[2], ${$_}[3]);
    }
    # Switches must come first.  Keep processing switches as long as
    # the next element begins with a dash
    while (@_ && $_[0] =~ /^-(.*)/) {
	# Get the switch with this name
	my $switch = $self->{SWITCHES}->{$1};
	$self->_barf("Unknown switch: -$1\n")
	    unless $switch;
	# Throw away the switch name
	shift;
	# Invoke the process code associated with this switch
	# FIXME:  How can switch be made implicit?
	@_ = $switch->{PROCESS}->($switch, $self, @_);
    }
    # Now that the switches have been handled, loop over the legal params
    foreach my $param (@{$self->{PARAMS}}) {
	# Bomb if a required arg wasn't provided
	$self->_barf("Not enough arguments; $param->{NAME} must be provided\n")
	    if (!@_ && $param->{REQUIRED});
	# If this is an all others param, grab all the remaining arguments
	if ($param->{ALLOTHERS}) {
	    $self->put($param->{NAME}, [@_]) if @_;
	    @_ = ();
	}
	# Otherwise, if there are arguments left, bind the next one to the parameter
	elsif (@_) {
	    $self->put($param->{NAME}, shift);
	}
    }
    # If any arguments are left over, the user botched it
    $self->_barf("Too many arguments\n")
	if (@_);
}

################################################################################

package SP::_Switch;

sub new {
    my $classname = shift;
    my $filename = shift;
    my $line = shift;
    my $self = {};
    bless($self, $classname);
    Logger->new()->NIST_die("Too few arguments to constructor while creating classname, at $filename line $line\n")
	unless @_ >= 2;
    # Switch name and documentation are always present
    $self->{NAME} = shift;
    $self->{DOCUMENTATION} = pop;
    $self->{USAGE} = "-$self->{NAME}";
    # I know, these are unnecessary
    $self->{PROCESS} = undef;
    $self->{CONSTANT} = undef;
    $self->{SUBVARS} = ();
    # Return two values
    # FIXME: Why won't [$self, \@_] work here?
    ($self, @_);
}

# Create new help switch
sub newHelp {
    my @args = new (@_);
    my $self = shift(@args);
    Logger->new()->NIST_die("Too many arguments to addHelpSwitch, at $_[1] line $_[2]\n")
	if (@args);
    # A help switch just prints out program usage then exits
    $self->{PROCESS} = sub {
	my $self = shift;
	my $sp = shift;
	$sp->showUsage();
	exit(0);
    };
    $self;
}

# Create a new constant switch
sub newConstant {
    my @args = new(@_);
    my $self = shift(@args);
    Logger->new()->NIST_die("Too few arguments to addConstantSwitch, at $_[1] line $_[2]\n")
	unless @args >= 1;
    Logger->new()->NIST_die("Too many arguments to addConstantSwitch, at $_[1] line $_[2]\n")
	unless @args <= 2;
    # Retrieve the constant value
    $self->{CONSTANT} = pop(@args);
    if (@args) {
	$self->{SUBVARS} = shift(@args);
	# Make sure, if there are subvars, that the number of subvars
	# matches the number of constant arguments
	Logger->new()->NIST_die("Number of values [" . join(", ", @{$self->{CONSTANT}}) .
	    "] does not match number of variables [" . join(", ", @{$self->{SUBVARS}}) .
		"], at $_[1] line $_[2]\n")
		    unless $#{$self->{CONSTANT}} == $#{$self->{SUBVARS}};
    }
    $self->{PROCESS} = sub {
	my $self = shift;
	my $sp = shift;
	my $counter = 0;
	$sp->put($self->{NAME}, $self->{CONSTANT});
	@_;
    };
    $self;
}

# Create a new var switch
sub newVar {
    my @args = new(@_);
    my $self = shift(@args);
    Logger->new()->NIST_die("Too many arguments to addVarSwitch, at $_[1] line $_[2]\n")
	unless @args <= 1;
    # If there are subvars
    if (@args) {
	my $arg = shift(@args);
	if (ref $arg) {
	    $self->{SUBVARS} = $arg;
	    # Augment the usage string with the name of the subvar
	    foreach my $subvar (@{$self->{SUBVARS}}) {
		$self->{USAGE} .= " <$subvar>";
	    }
	    # A var switch with subvars binds each subvar
	    $self->{PROCESS} = sub {
		my $self = shift;
		my $sp = shift;
		my $counter = 0;
		my $value = [];
		# Make sure there are enough arguments for this switch
		foreach (@{$self->{SUBVARS}}) {
		    $sp->_barf("Not enough arguments to switch -$self->{NAME}\n")
			unless @_;
		    push(@{$value}, shift);
		}
		$sp->put($self->{NAME}, $value);
		@_;
	    };
	}
	else {
	    $self->{USAGE} .= " <$arg>";
	    $self->{PROCESS} = sub {
		my $self = shift;
		my $sp = shift;
		$sp->put($self->{NAME}, shift);
		@_;
	    };
	}
    }
    else {
	# A var switch without subvars gets one argument, called 'value'
	# in the usage string
	$self->{USAGE} .= " <value>";
	# Bind the argument to the parameter
	$self->{PROCESS} = sub {
	    my $self = shift;
	    my $sp = shift;
	    $sp->put($self->{NAME}, shift);
	    @_;
	};
    }
    $self;
}

# Create a new immediate switch
sub newImmediate {
    my @args = new(@_);
    my $self = shift(@args);
    Logger->new()->NIST_die("Wrong number of arguments to addImmediateSwitch or addMetaSwitch, at $_[1] line $_[2]\n")
	unless @args == 1;
    $self->{PROCESS} = shift(@args);
    $self;
}

# Create a new meta switch
sub newMeta {
    # The call looks just like a call to newImmediate, except that
    # instead of a fn as the second argument, there's a hashref.  So
    # use newImmediate to do the basic work, then strip out the
    # hashref and replace it with the required function.
    my $self = newImmediate(@_);
    $self->{METAMAP} = $self->{PROCESS};
    $self->{PROCESS} = sub {
	my $var;
	my $val;
	my $self = shift;
	my $sp = shift;
	# FIXME: Doesn't properly handle case where var is itself a metaswitch
	while (($var, $val) = each %{$self->{METAMAP}}) {
	    $sp->put($var, $val);
	}
	@_;
    };
    $self;
}

################################################################################

package SP::_Param;

# A parameter is just a struct for the four args
sub new {
    my $classname = shift;
    my $filename = shift;
    my $line = shift;
    my $self = {};
    bless($self, $classname);
    $self->{NAME} = shift;
    # param name and documentation are first and last, respectively.
    $self->{DOCUMENTATION} = pop;
    $self->{USAGE} = $self->{NAME};
    # If omitted, REQUIRED and ALLOTHERS default to undef
    $self->{REQUIRED} = shift;
    $self->{ALLOTHERS} = shift;
    # Tack on required to the documentation stream if this arg is required
    $self->{DOCUMENTATION} .= " (Required)."
	if ($self->{REQUIRED});
    $self;
}

################################################################################

### END INCLUDE Switches