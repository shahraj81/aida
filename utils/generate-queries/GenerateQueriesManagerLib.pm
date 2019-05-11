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
  DUPLICATE_IN_POOLED_RESPONSE            DEBUG_INFO     Response: %s already in pool therefore skipping
  DUPLICATE_QUERY                         DEBUG_INFO     Query %s (file: %s) is a duplicate of %s (file: %s) therefore skipping it
  DISCONNECTED_VALID_GRAPH                WARNING        Considering only valid edges, the graph in submission is not fully connected
  GROUND_TRUTH                            DEBUG_INFO     GROUND_TRUTH_INFO: %s     
  MULTIPLE_INCOMPATIBLE_ZH_ASSESSMENTS    ERROR          Multiple incompatible assessments provided (node: %s, mention_span: %s)
  EXTRA_EDGE_JUSTIFICATIONS               WARNING        Extra edge justifications (expected <= %s; provided %s)
  INVALID_CONFIDENCE                      WARNING        Invalid confidence %s in response
  INVALID_END                             WARNING        Invalid end %s in response justification of type %s
  INVALID_JUSTIFICATION_TYPE              ERROR          Invalid justification type %s
  INVALID_KEYFRAMEID                      WARNING        Invalid keyframeid %s 
  INVALID_START                           WARNING        Invalid start %s in %s
  MISMATCHING_COLUMNS                     FATAL_ERROR    Mismatching columns (header:%s, entry:%s) %s %s
  MISSING_FILE                            FATAL_ERROR    Could not open %s: %s
  MULTIPLE_JUSTIFYING_DOCS                ERROR          Multiple justifying documents: %s (expected only one)
  MULTIPLE_POTENTIAL_ROOTS                FATAL_ERROR    Multiple potential roots "%s" in query DTD file: %s
  NO_FQEC_FOR_CORRECT_ENTRY               ERROR          No FQEC found for a correct entry
  NONNUMERIC_END                          WARNING        End %s is not numeric
  NONNUMERIC_START                        WARNING        Start %s is not numeric
  PARAMETER_KEY_EXISTS                    WARNING        Key %s used multiple times
  RESPONSE_ASSESSMENT                     DEBUG_INFO     ASSESSMENT_INFO: %s
  RUNS_HAVE_MULTIPLE_TASKS                ERROR          Response files in the pathfile include task1 and task2 responses; expected responses files corresponding to exactly one task 
  UNDEFINED_FUNCTION                      FATAL_ERROR    Function %s not defined in package %s
  UNEXPECTED_ENTTYPE                      WARNING        Unexpected enttype %s in response (expected %s)
  UNEXPECTED_OUTPUT_TYPE                  FATAL_ERROR    Unknown output type %s
  UNEXPECTED_PARAMETER_LINE               WARNING        Unexpected line in the parameters file
  UNEXPECTED_QUERY_TYPE                   FATAL_ERROR    Unexpected query type %s
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

sub get_num_problems {
	my ($self) = @_;
	$self->get_num_errors() + $self->get_num_warnings();
}

sub get_error_type {
  my ($self, $error_name) = @_;
  $self->{FORMATS}{$error_name}{TYPE};
}

# NIST submission scripts demand an error code of 255 on failure
my $NIST_error_code = 255;

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
  my ($class, $logger, $filename) = @_;
  my $self = {
    CLASS => 'Parameters',
    FILENAME => $filename,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load() if $filename;
  $self;
}

sub load {
	my ($self) = @_;
	my $filename = $self->get("FILENAME");
	open(my $infile, "<:utf8", $filename) 
		or $self->get("LOGGER")->NIST_die("Could not open $filename: $!");
	my $linenum = 0;
	while(my $line = <$infile>) {
		$linenum++;
		chomp $line;
		$line =~ s/\s+//g;
		next if $line =~ /^\#/;
		next if $line =~ /^$/;
		if($line =~ /^(.*?)\=\>(.*?)$/){
			my ($key, $value) = ($1, $2);
			if($self->get("$key") eq "nil") {
				$self->set($key, $value);
			}
			else {
				$self->get("LOGGER")->record_problem(
						"PARAMETER_KEY_EXISTS", $key,
						{FILENAME=>$filename, LINENUM=>$linenum});
			}
		}
		else{
			$self->get("LOGGER")->record_problem(
					"UNEXPECTED_PARAMETER_LINE", 
					{FILENAME=>$filename, LINENUM=>$linenum});
		}
	}
	close($infile);
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
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'Node');
  $self->{CLASS} = 'Nodes';
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
		LINENUM => 0,
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
	$self->get("STRING_TO_OBJECT", $object_string, $search_node, $self->get("OBJECT_WHERE")->{LINENUM});
}

sub get_STRING_TO_OBJECT {
	my ($self, $object_string, $search_node, $linenum) = @_;
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
				my $new_where = {FILENAME=>$self->get("OBJECT_WHERE")->{FILENAME}, LINENUM=>$linenum}; 
				return XMLElement->new($logger, $value, $search_tag, $new_line, $xml_attributes, $new_where);
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
				my $new_where = {FILENAME=>$self->get("OBJECT_WHERE")->{FILENAME}, LINENUM=>$linenum}; 
				return XMLElement->new($logger, $xml_child_object, $search_tag, 1, $xml_attributes, $new_where);
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
		my $found_linenum = $linenum;
		my $containerfound_linenum = $linenum;
		my $xml_container = XMLContainer->new($logger);
		my $new_search_tag;
		foreach my $line(split(/\n/, $object_string)){
			chomp $line;
			$linenum++;
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
						$found_linenum = $linenum;
						$check_next_child = 0;
						# Handle cases like <tag.*?> value <\/tag>
						if($line =~ /\<\/$new_search_tag\>/) {
							my $child_node = $self->get("DTD")->get("TREE")->get("NODE", $this_child_allowed_type);
							my $xml_child_object = $self->get("STRING_TO_OBJECT", $new_object_string, $child_node, $found_linenum);
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
					my $xml_child_object = $self->get("STRING_TO_OBJECT", $new_object_string, $child_node, $found_linenum);
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
		my $new_where = {FILENAME=>$self->get("OBJECT_WHERE")->{FILENAME}, LINENUM=>$containerfound_linenum}; 
		return XMLElement->new($logger, $xml_container, $search_tag, 1, $xml_attributes, $new_where);
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
	my ($class, $logger, $queries, $docid_mappings, $dtd_filename, @xml_filenames) = @_;
	my $self = {
		CLASS => 'ResponseSet',
		QUERIES => $queries,
		DTD_FILENAME => $dtd_filename,
		XML_FILENAMES => [@xml_filenames],
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
	my @xml_filenames = @{$self->get("XML_FILENAMES")};
	my $query_type = $self->get("QUERIES")->get("QUERYTYPE");
	my $docid_mappings = $self->get("DOCID_MAPPINGS");
	my $queries = $self->get("QUERIES");
	my $i = 0;
	foreach my $xml_filename(@xml_filenames) {
		my $task = "task1";
		$task = "task2" if $xml_filename =~ /TA2.*_responses.xml$/;
		$self->set("TASK", $task) if $self->get("TASK") eq "nil";
		$logger->record_problem("RUNS_HAVE_MULTIPLE_TASKS", {FILENAME => __FILE__, LINENUM => __LINE__})
			if($task ne $self->get("TASK"));
		my $xml_filehandler = XMLFileHandler->new($logger, $dtd_filename, $xml_filename);
		while(my $xml_response_object = $xml_filehandler->get("NEXT_OBJECT")) {
			$i++;
			my $response;
			$response = ClassResponse->new($logger, $xml_response_object, $xml_filename, $queries, $docid_mappings) if($query_type eq "class_query");
			$response = ZeroHopResponse->new($logger, $xml_response_object, $xml_filename, $queries, $docid_mappings) if($query_type eq "zerohop_query");
			$response = GraphResponse->new($logger, $xml_response_object, $xml_filename, $queries, $docid_mappings) if($query_type eq "graph_query");
			$self->get("RESPONSES")->add($response, $i) if $response->is_valid();
		}
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
# Pool
#####################################################################################

package Pool;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $filename) = @_;
  my $self = $class->SUPER::new($logger, 'Kit');
  $self->{CLASS} = 'Pool';
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self->load($filename) if $filename;
  $self;
}

sub load {
	my ($self, $filename) = @_;
	my $logger = $self->get("LOGGER");
	my $filehandler = FileHandler->new($logger, $filename);
	my $entries = $filehandler->get("ENTRIES");
	foreach my $entry($entries->toarray()) {
		my $kb_id = $entry->get("KBID");
		my $kbid_kit = $self->get("BY_KEY", $kb_id);
		my $value = $entry->get("LINE");
		my $key = &main::generate_uuid_from_string($value);
		$kbid_kit->add($value, $key) unless $self->exists($key);
	}
}

#####################################################################################
# Kit
#####################################################################################

package Kit;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'KitEntry');
  $self->{CLASS} = 'Pool';
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

#####################################################################################
# KitEntry
#####################################################################################

package KitEntry;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = {
    CLASS => 'KitEntry',
    TYPE => undef,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub tostring {
	my ($self) = @_;
	my $type = $self->get("TYPE");
	
	my $method = $self->can("tostring_$type");
  return $method->($self) if $method;
  return "nil";
}

sub tostring_zerohop_query {
	my ($self) = @_;
	my ($query_id, $enttype, $id, $mention_modality, $docid, $mention_span, $label_1, $label_2)
		= map {$self->get($_)} qw(KB_ID ENTTYPE ID MENTION_MODALITY DOCID MENTION_SPAN LABEL_1 LABEL_2);
	join("\t", ($query_id, $enttype, $id, $mention_modality, $docid, $mention_span, $label_1, $label_2));
}

#####################################################################################
# ResponsesPool
#####################################################################################

package ResponsesPool;

use parent -norequire, 'Super';

sub new {
	my ($class, $logger, $k, $core_docs, $docid_mappings, $queries, $ldc_queries, $responses_dtd_file, $responses_xml_pathfile, $previous_pool) = @_;
	my $self = {
		CLASS => 'ResponsesPool',
		CORE_DOCS => $core_docs,
		DOCID_MAPPINGS => $docid_mappings,
		K => $k,
		LDC_QUERIES => $ldc_queries,
		PREVIOUS_POOL => $previous_pool,
		QUERIES => $queries,
		QUERYTYPE => $queries->get("QUERYTYPE"),
		RESPONSES_DTD_FILENAME => $responses_dtd_file,
		RESPONSES_XML_PATHFILE => $responses_xml_pathfile,
		RESPONSES_POOL => undef,
		LOGGER => $logger,
	};
	bless($self, $class);
	$self->load();
	$self;
}

sub load {
	my ($self) = @_;
	my $logger = $self->get("LOGGER");
	my $core_docs = $self->get("CORE_DOCS");
	my $docid_mappings = $self->get("DOCID_MAPPINGS");
	my $k = $self->get("K");
	my $queries = $self->get("QUERIES");
	my $ldc_queries = $self->get("LDC_QUERIES");
	my $responses_dtd_file = $self->get("RESPONSES_DTD_FILENAME");
	my $responses_xml_pathfile = $self->get("RESPONSES_XML_PATHFILE");
	my $query_type = $self->get("QUERYTYPE");
	my $previous_pool = $self->get("PREVIOUS_POOL");
	my $responses_pool;
	$responses_pool = ClassResponsesPool->new($logger, $k, $core_docs, $docid_mappings, $queries, $ldc_queries, $responses_dtd_file, $responses_xml_pathfile, $previous_pool) if($query_type eq "class_query");
	$responses_pool = ZeroHopResponsesPool->new($logger, $k, $core_docs, $docid_mappings, $queries, $ldc_queries, $responses_dtd_file, $responses_xml_pathfile, $previous_pool) if($query_type eq "zerohop_query");
	$responses_pool = GraphResponsesPool->new($logger, $k, $core_docs, $docid_mappings, $queries, $ldc_queries, $responses_dtd_file, $responses_xml_pathfile, $previous_pool) if($query_type eq "graph_query");
	$self->set("RESPONSES_POOL", $responses_pool);
}

sub write_output {
	my ($self, $program_output) = @_;
	$self->get("RESPONSES_POOL")->write_output($program_output);
}

#####################################################################################
# ZeroHopResponsesPool
#####################################################################################

package ZeroHopResponsesPool;

use parent -norequire, 'Super';

sub new {
	my ($class, $logger, $k, $core_docs, $docid_mappings, $queries, $ldc_queries, $responses_dtd_file, $responses_xml_pathfile, $entire_pool) = @_;
	my $self = {
		CLASS => 'ZeroHopResponsesPool',
		CORE_DOCS => $core_docs,
		DOCID_MAPPINGS => $docid_mappings,
		ENTIRE_POOL => $entire_pool,
		K => $k,
		LDC_QUERIES => $ldc_queries,
		QUERIES => $queries,
		QUERYTYPE => $queries->get("QUERYTYPE"),
		RESPONSES_DTD_FILENAME => $responses_dtd_file,
		RESPONSES_XML_PATHFILE => $responses_xml_pathfile,
		RESPONSES_POOL => undef,
		LOGGER => $logger,
	};
	bless($self, $class);
	$self->load();
	$self;
}

sub load {
	my ($self) = @_;
	my $logger = $self->get("LOGGER");
	my $core_docs = $self->get("CORE_DOCS");
	my $docid_mappings = $self->get("DOCID_MAPPINGS");
	my $k = $self->get("K");
	my $queries = $self->get("QUERIES");
	my $ldc_queries = $self->get("LDC_QUERIES");
	my $responses_dtd_file = $self->get("RESPONSES_DTD_FILENAME");
	my $responses_xml_pathfile = $self->get("RESPONSES_XML_PATHFILE");
	my $query_type = $self->get("QUERYTYPE");
	my $entire_pool = $self->get("ENTIRE_POOL");
	$entire_pool = Pool->new($logger) if $entire_pool eq "nil";
	
	my $filehandler = FileHandler->new($logger, $responses_xml_pathfile);
	my $entries = $filehandler->get("ENTRIES");
	foreach my $entry($entries->toarray()) {
		my $responses_xml_file = $entry->get("filename");
		print STDERR "--processing $responses_xml_file\n";
		my $validated_responses = ResponseSet->new($logger, $queries, $docid_mappings, $responses_dtd_file, $responses_xml_file);
		foreach my $response($validated_responses->get("RESPONSES")->toarray()) {
			my $query_id = $response->get("QUERYID");
			my $kb_id = $ldc_queries->get("QUERY", $query_id)->get("ENTRYPOINT")->get("NODE")
				if $ldc_queries->get("QUERY", $query_id);
			next unless $kb_id;
			$kb_id =~ s/^\?//;
			my $kbid_kit = $entire_pool->get("BY_KEY", $kb_id);
			my $enttype = $queries->get("QUERY", $query_id)->get("ENTRYPOINT")->get("ENTTYPE");
			# Making the enttype NIL as desired by LDC
			$enttype = "NIL";
			my $source_docid = $response->get("RESPONSE_DOCID_FROM_FILENAME");
			my $scope = $response->get("SCOPE");
			my %kit_entries_by_docids;
			foreach my $justification(sort {$b->get("CONFIDENCE") <=> $a->get("CONFIDENCE")} $response->get("JUSTIFICATIONS")->toarray()) {
				my $mention_span = $justification->tostring();
				my $mention_modality = $justification->get("MODALITY");
				my $confidence = $justification->get("CONFIDENCE");
				my @docids = $justification->get("DOCIDS", $docid_mappings, $scope);
				@docids = grep {$_ eq $source_docid} @docids if $source_docid;
				foreach my $docid(@docids) {
					next unless $core_docs->exists($docid);
					my $kit_entry = KitEntry->new($logger);
					$kit_entry->set("TYPE", $query_type);
					$kit_entry->set("KB_ID", $kb_id);
					$kit_entry->set("ENTTYPE", $enttype);
					$kit_entry->set("ID", "<ID>");
					$kit_entry->set("MENTION_MODALITY", $mention_modality);
					$kit_entry->set("DOCID", $docid);
					$kit_entry->set("MENTION_SPAN", $mention_span);
					$kit_entry->set("LABEL_1", "NIL");
					$kit_entry->set("LABEL_2", "NIL");
					$kit_entry->set("CONFIDENCE", $confidence);
					my $key = &main::generate_uuid_from_string($kit_entry->tostring());
					$kit_entries_by_docids{"$docid-$mention_modality"}{$key} = $kit_entry;
				}
			}
			foreach my $docid_modality (keys %kit_entries_by_docids) {
				my $i = 0;
				foreach my $key(sort {$kit_entries_by_docids{$docid_modality}{$b}->get("CONFIDENCE") <=> $kit_entries_by_docids{$docid_modality}{$a}->get("CONFIDENCE")} 
										keys %{$kit_entries_by_docids{$docid_modality}}) {
					$i++;
					last if $i > $k;
					my $kit_entry = $kit_entries_by_docids{$docid_modality}{$key};
					my $value = $kit_entry->tostring();
					$kbid_kit->add($value, $key) unless $kbid_kit->exists($key);
				}
			}
		}
	}
	$self->set("RESPONSES_POOL", $entire_pool);
}

sub write_output {
	my ($self, $program_output) = @_;
	my $pool = $self->get("RESPONSES_POOL");
	my $header = join("\t", qw(KBID CLASS ID MODALITY DOCID SPAN CORRECTNESS TYPE));
	print "$header\n";
	foreach my $kb_id($pool->get("ALL_KEYS")) {
		my $kit = $pool->get("BY_KEY", $kb_id);
		foreach my $output_line($kit->toarray()) {
			print $program_output "$output_line\n";
		}
	}
}

#####################################################################################
# PrevailingTheoryEntry
#####################################################################################

package PrevailingTheoryEntry;

use parent -norequire, 'Super';

sub new {
	my ($class, $logger, $entry) = @_;
	my $self = {
		CLASS => 'PrevailingTheoryEntry',
		ENTRY => $entry,
		MATRIX_KE_ITEM_NUM => $entry->get("Matrix KE Item Number"),
		ONTOLOGY_ID => $entry->get("Ontology ID"),
	  ARGUMENT_KBID => $entry->get("Argument KB ID"),
	  ITEM_KE => $entry->get("Item KE"),
	  TYPE => $entry->get("Type"),
	  SUBTYPE => $entry->get("Subtype"),
	  SUBSUBTYPE => $entry->get("Sub-subtype"),
		LOGGER => $logger,
	};
	bless($self, $class);
	$self;
}

#####################################################################################
# ArgumentSpec
#####################################################################################

package ArgumentSpec;

use parent -norequire, 'Super';

sub new {
	my ($class, $logger, $entry, $argnum) = @_;
	my $self = {
		CLASS => 'ArgumentSpec',
		ENTRY => $entry,
		ARGUMENT_NUM => $argnum,
		LABEL => $entry->get("arg" . $argnum . " " . "label"),
		OUTPUT_VALUE => $entry->get("Output value for arg" . $argnum),
		LOGGER => $logger,
	};
	bless($self, $class);
	$self;
}

#####################################################################################
# EntitySpec
#####################################################################################

package EntitySpec;

use parent -norequire, 'Super';

sub new {
	my ($class, $logger, $entry) = @_;
	my $self = {
		CLASS => 'EntitySpec',
		ENTRY => $entry,
		ANNOTATION_ID => $entry->get("AnnotIndexID"),
		TYPE => $entry->get("Type"),
		SUBTYPE => $entry->get("Subtype"),
		SUBSUBTYPE => $entry->get("Sub-subtype"),
		TYPE_OV => $entry->get("Output Value for Type"),
		SUBTYPE_OV => $entry->get("Output Value for Subtype"),
		SUBSUBTYPE_OV => $entry->get("Output Value for Sub-subtype"),
		LOGGER => $logger,
	};
	bless($self, $class);
	$self;
}

#####################################################################################
# EventSpec
#####################################################################################

package EventSpec;

use parent -norequire, 'Super';

sub new {
	my ($class, $logger, $entry) = @_;
	my $self = {
		CLASS => 'EventSpec',
		ENTRY => $entry,
		ARGUMENTS => Container->new($logger),
		ANNOTATION_ID => $entry->get("AnnotIndexID"),
		TYPE => $entry->get("Type"),
		SUBTYPE => $entry->get("Subtype"),
		SUBSUBTYPE => $entry->get("Sub-subtype"),
		TYPE_OV => $entry->get("Output Value for Type"),
		SUBTYPE_OV => $entry->get("Output Value for Subtype"),
		SUBSUBTYPE_OV => $entry->get("Output Value for Sub-subtype"),
		LOGGER => $logger,
	};
	bless($self, $class);
	for(my $argnum = 1; $argnum <= 5; $argnum++) {
		$self->{ARGUMENTS}->add(
			ArgumentSpec->new($logger, $entry, $argnum), 
			"arg" . $argnum
		);
	}
	$self;
}

sub get_FULL_TYPE {
	my ($self) = @_;
	my ($type, $subtype, $subsubtype) = map {$self->get($_)} qw(TYPE SUBTYPE SUBSUBTYPE);
	my $full_type = $type;
	$full_type = "$type.$subtype" if $subtype ne "n/a";
	$full_type = "$type.$subtype.$subsubtype" if $subtype ne "n/a" && $subsubtype ne "n/a";
	$full_type;	
}

#####################################################################################
# RelationSpec
#####################################################################################

package RelationSpec;

use parent -norequire, 'Super';

sub new {
	my ($class, $logger, $entry) = @_;
	my $self = {
		CLASS => 'RelationSpec',
		ENTRY => $entry,
		ARGUMENTS => Container->new($logger),
		ANNOTATION_ID => $entry->get("AnnotIndexID"),
		TYPE => $entry->get("Type"),
		SUBTYPE => $entry->get("Subtype"),
		SUBSUBTYPE => $entry->get("Sub-Subtype"),
		TYPE_OV => $entry->get("Output Value for Type"),
		SUBTYPE_OV => $entry->get("Output Value for Subtype"),
		SUBSUBTYPE_OV => $entry->get("Output Value for Sub-Subtype"),
		LOGGER => $logger,
	};
	bless($self, $class);
	for(my $argnum = 1; $argnum <= 2; $argnum++) {
		$self->{ARGUMENTS}->add(
			ArgumentSpec->new($logger, $entry, $argnum), 
			"arg" . $argnum
		);
	}
	$self;
}

sub get_FULL_TYPE {
	my ($self) = @_;
	my ($type, $subtype, $subsubtype) = map {$self->get($_)} qw(TYPE SUBTYPE SUBSUBTYPE);
	my $full_type = $type;
	$full_type = "$type.$subtype" if $subtype ne "n/a";
	$full_type = "$type.$subtype.$subsubtype" if $subtype ne "n/a" && $subsubtype ne "n/a";
	$full_type;	
}

#####################################################################################
# PrevailingTheoryContainer
#####################################################################################

package PrevailingTheoryContainer;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, "Container");
  $self->{CLASS} = 'PrevailingTheoryContainer';
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

#####################################################################################
# OntologyContainer
#####################################################################################

package OntologyContainer;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger);
  $self->{CLASS} = 'OntologyContainer';
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

sub get_RELATION_WITH_ITEM_KE {
	my ($self, $item_ke) = @_;
	my $spec;
	foreach my $ontology_id($self->get("ALL_KEYS")) {
		next unless $ontology_id =~ /^LDC_rel_/;
		$spec = $self->get("BY_KEY", $ontology_id);
		foreach my $argument_num($spec->get("ARGUMENTS")->get("ALL_KEYS")) {
			my $argument = $spec->get("ARGUMENTS")->get("BY_KEY", $argument_num);
			return ($spec, $argument) if $argument->get("OUTPUT_VALUE") eq $item_ke;
		}
	}}

sub get_EVENT_WITH_ITEM_KE {
	my ($self, $item_ke) = @_;
	my $spec;
	foreach my $ontology_id($self->get("ALL_KEYS")) {
		next unless $ontology_id =~ /^LDC_evt_/;
		$spec = $self->get("BY_KEY", $ontology_id);
		foreach my $argument_num($spec->get("ARGUMENTS")->get("ALL_KEYS")) {
			my $argument = $spec->get("ARGUMENTS")->get("BY_KEY", $argument_num);
			return ($spec, $argument) if $argument->get("OUTPUT_VALUE") eq $item_ke;
		}
	}
}

#####################################################################################
# QueryGenerator
#####################################################################################

package QueryGenerator;

use parent -norequire, 'Super';

sub new {
	my ($class, $logger, $parameters) = @_;
	my $self = {
		CLASS => 'QueryGenerator',
		TA1_CLASS_QUERIES => undef,
		TA1_GRAPH_QUERIES => undef,
		TA2_ZEROHOP_QUERIES => undef,
		TA2_GRAPH_QUERIES => undef,
		ENTITIES => OntologyContainer->new($logger),
		RELATIONS => OntologyContainer->new($logger),
		EVENTS => OntologyContainer->new($logger),
		PREVAILING_THEORY_ENTRIES => PrevailingTheoryContainer->new($logger),
		NEXT_TASK1_CLASS_QUERY_NUM => 1,
		NEXT_TASK1_GRAPH_QUERY_NUM => 1,
		NEXT_TASK2_ZEROHOP_QUERY_NUM => 1,
		NEXT_TASK2_GRAPH_QUERY_NUM => 1,
		PARAMETERS => $parameters,
		LOGGER => $logger,
	};
	bless($self, $class);
	$self->load();
	$self;
}

sub load {
	my ($self, $field, @arguments) = @_;
  $field = "MAIN" unless $field;
  my $method = $self->can("load_$field");
  return $method->($self, @arguments) if $method;
}

sub load_MAIN {
	my ($self) = @_;
	my $parameters = $self->get("PARAMETERS");
	foreach my $key($parameters->get("ONTOLOGY_FILES")->get("ALL_KEYS")) {
		my $filename = $parameters->get("ONTOLOGY_FILES")->get("BY_KEY", $key);
		$self->load("ONTOLOGY", $key, $filename);
	}
	foreach my $key($parameters->get("PREVAILING_THEORY_FILES")->get("ALL_KEYS")) {
		my $filename = $parameters->get("PREVAILING_THEORY_FILES")->get("BY_KEY", $key);
		$self->load("PREVAILING_THEORY", $key, $filename);
	}
}

sub load_ONTOLOGY {
	my ($self, $ontology_type, $filename) = @_;
	my $filehandler = FileHandler->new($self->get("LOGGER"), $filename);
	my $ontology_container = $self->get(uc($ontology_type));
	foreach my $entry($filehandler->get("ENTRIES")->toarray()) {
		my $ontology_id = $entry->get("AnnotIndexID");
		my $spec;
		$spec = EntitySpec->new($self->get("LOGGER"), $entry) if $ontology_type eq "entities";
		$spec = EventSpec->new($self->get("LOGGER"), $entry) if $ontology_type eq "events";
		$spec = RelationSpec->new($self->get("LOGGER"), $entry) if $ontology_type eq "relations";
		$ontology_container->add($spec, $ontology_id);
	}
}

sub load_PREVAILING_THEORY {
	my ($self, $key, $filename) = @_;
	$key = uc($key);
	my $prevailing_theory_container = $self->get("PREVAILING_THEORY_ENTRIES");
	my $subcontainer = $prevailing_theory_container->get("BY_KEY", $key);
	my $filehandler = FileHandler->new($self->get("LOGGER"), $filename);
	foreach my $entry($filehandler->get("ENTRIES")->toarray()) {
		my $pt_entry = PrevailingTheoryEntry->new($self->get("LOGGER"), $entry);
		$subcontainer->add($pt_entry);
	}
}

#		my $filehandler = FileHandler->new($self->get("LOGGER"), $filename);
#		my $entries = $filehandler->get("ENTRIES");
#		foreach my $entry($entries->toarray()) {
#			my ($doceid, $segment_id, $start_char, $end_char) =
#				map {$entry->get($_)} qw(doceid segment_id start_char end_char);
#			my $segments = $self->get("BY_KEY", $doceid);
#			my $sentence_boundary = $segments->get("BY_KEY", "$doceid:$segment_id");
#			$sentence_boundary->set("SEGMENT_ID", $segment_id);
#			$sentence_boundary->set("START_CHAR", $start_char);
#			$sentence_boundary->set("END_CHAR", $end_char);


sub generate_queries {
	my ($self, $year, $topic_id, $prevailing_theory_id) = @_;
	$self->generate_task1_class_queries($year, $topic_id, $prevailing_theory_id);
	$self->generate_task1_graph_queries($year, $topic_id, $prevailing_theory_id);
	$self->generate_task2_zerohop_queries($year, $topic_id, $prevailing_theory_id);
  $self->generate_task2_graph_queries($year, $topic_id, $prevailing_theory_id);	
  
  foreach my $queries_container_name(qw(TA1_CLASS_QUERIES TA1_GRAPH_QUERIES TA2_ZEROHOP_QUERIES TA2_GRAPH_QUERIES)) {
  	$self->get($queries_container_name)->write_to_file();
  }
}

sub generate_graph_queries {
	my ($self, $year, $topic_id, $prevailing_theory_id, $task) = @_;
	my $task_long_name = $task;
	my $task_short_name = "TA1";
	$task_short_name ="TA2" if $task eq "task2";
	my $logger = $self->get("LOGGER");
	my $dtd_file = $self->get("PARAMETERS")->get("DTD_FILES")->get("BY_KEY", "graph_query");
	my $output_dir = $self->get("PARAMETERS")->get("OUTPUT_DIR");
	system("mkdir -p $output_dir");
	my $xml_file = "$output_dir/" . $task_long_name . "\_graph_queries.xml";
	my $queries = $self->get($task_short_name . "_GRAPH_QUERIES");
	if ($queries eq "nil") {
		$queries = QuerySet->new($logger, $dtd_file, $xml_file);
		$self->set($task_short_name . "_GRAPH_QUERIES", $queries);
	}
	my $subcontainer = $self->get("PREVAILING_THEORY_ENTRIES")->get("BY_KEY", $topic_id . "_" . $prevailing_theory_id);
	my $query_id_prefix = $self->get("PARAMETERS")->get($task_short_name . "_GRAPH_QUERYID_PREFIX");
	my $reference_kbid_prefix = $self->get("PARAMETERS")->get("REFERENCE_KBID_PREFIX");
	my %edge_label_and_argkbids_used;
	foreach my $pt_entry($subcontainer->toarray()) {
		my $argument_kbid = $pt_entry->get("ARGUMENT_KBID");
		# For task1, we need only distict edge labels for queryids
		$argument_kbid = 0 if $task_long_name eq "task1";
		next unless $argument_kbid =~ /^\d+$/;
		my $role;
		if($pt_entry->get("ONTOLOGY_ID") =~ /^LDC_ent_/) {
			my $item_ke = $pt_entry->get("ITEM_KE");
			my $subject_spec;
			if($item_ke =~ /^(evt|rel)\d/) {
				my ($event_or_relation_spec, $argument_spec);
				($event_or_relation_spec, $argument_spec)
					= $self->get("EVENTS")->get("EVENT_WITH_ITEM_KE", $item_ke)
						if $item_ke =~ /^evt\d/;
				($event_or_relation_spec, $argument_spec)
					= $self->get("RELATIONS")->get("RELATION_WITH_ITEM_KE", $item_ke)
						if $item_ke =~ /^rel\d/;
				my $event_or_relation_type = $event_or_relation_spec->get("FULL_TYPE");
				my $argument_label = $argument_spec->get("LABEL");
				my $edge_label = $event_or_relation_type . "_" . $argument_label;
				next if $edge_label_and_argkbids_used{$edge_label . "_" . $argument_kbid};
				my $i = $self->get("NEXT_" . uc($task_long_name) . "_GRAPH_QUERY_NUM");
				my $query_id = "$query_id_prefix\_$i";
				my $query_reference_kbid = $reference_kbid_prefix . ":" . $argument_kbid;
				my $sparql = $self->get($task_short_name . "_GRAPH_SPARQL_QUERY_TEMPLATE");
				$sparql =~ s/\[__QUERY_ID__\]/$query_id/gs;
				$sparql =~ s/\[__PREDICATE__\]/$edge_label/gs;
				$sparql =~ s/\[__KBID__\]/$query_reference_kbid/gs if $task_long_name eq "task2";
				my $query_attributes = XMLAttributes->new($logger);
				$query_attributes->add("$query_id", "id");
				my $xml_subject = XMLElement->new($logger, "?subject", "subject", 0);
				my $xml_predicate = XMLElement->new($logger, $edge_label, "predicate", 0);
				my $xml_object;
				$xml_object = XMLElement->new($logger, "?object", "object", 0)
					if $task_long_name eq "task1";
				$xml_object = XMLElement->new($logger, $query_reference_kbid, "object", 0)
					if $task_long_name eq "task2";
				my $xml_sparql = XMLElement->new($logger, $sparql, "sparql", 1);
				my $xml_query = XMLElement->new($logger,
							XMLContainer->new($logger, $xml_subject, $xml_predicate, $xml_object, $xml_sparql),
							"graph_query",
							1,
							$query_attributes);
				my $query = GraphQuery->new($logger, $xml_query);
				$queries->add($query);
				$self->increment("NEXT_" . uc($task_long_name) . "_GRAPH_QUERY_NUM");
				$edge_label_and_argkbids_used{$edge_label . "_" . $argument_kbid} = 1;
			}
		}
	}
}

sub generate_task1_class_queries {
	my ($self, $year, $topic_id, $prevailing_theory_id) = @_;
	my $logger = $self->get("LOGGER");
	my $dtd_file = $self->get("PARAMETERS")->get("DTD_FILES")->get("BY_KEY", "class_query");
	my $output_dir = $self->get("PARAMETERS")->get("OUTPUT_DIR");
	system("mkdir -p $output_dir");
	my $xml_file = "$output_dir/task1_class_queries.xml";
	my $queries = $self->get("TA1_CLASS_QUERIES");
	if ($queries eq "nil") {
		$queries = QuerySet->new($logger, $dtd_file, $xml_file);
		$self->set("TA1_CLASS_QUERIES", $queries); 
	}
	my $subcontainer = $self->get("PREVAILING_THEORY_ENTRIES")->get("BY_KEY", $topic_id . "_" . $prevailing_theory_id);
	my $query_id_prefix = $self->get("PARAMETERS")->get("TA1_CLASS_QUERYID_PREFIX");
	my %types_used;
	foreach my $pt_entry($subcontainer->toarray()) {
		# Is this an entity involved in the prevailing theory?
		my $ontology_id = $pt_entry->get("ONTOLOGY_ID");
		if($ontology_id =~ /^LDC_ent_/) {
			# If yes, pick up its type, subtype and subsubtypes from ontology file
			my $entity_spec = $self->get("ENTITIES")->get("BY_KEY", $ontology_id);
			my ($type, $subtype, $subsubtype) = map {$entity_spec->get($_)} qw(TYPE SUBTYPE SUBSUBTYPE);
			my @query_types = ($type);
			push(@query_types, "$type.$subtype") if $subtype ne "n/a";
			push(@query_types, "$type.$subtype.$subsubtype") if $subtype ne "n/a" && $subsubtype ne "n/a";
			foreach my $query_type(@query_types) {
				next if $types_used{$query_type};
				# Generate a query at all granularities
				my $i = $self->get("NEXT_TASK1_CLASS_QUERY_NUM");
				my $query_id = "$query_id_prefix\_$i";		
				# Generate the XML object corresponding to the query
				my $sparql = $self->get("TA1_CLASS_SPARQL_QUERY_TEMPLATE");
				$sparql =~ s/\[__QUERY_ID__\]/$query_id/gs;
				$sparql =~ s/\[__TYPE__\]/$query_type/gs;
				my $query_attributes = XMLAttributes->new($logger);
				$query_attributes->add("$query_id", "id");
				my $xml_doceid = XMLElement->new($logger, $query_type, "enttype", 0);
				my $xml_sparql = XMLElement->new($logger, $sparql, "sparql", 1);
				my $xml_object = XMLElement->new($logger,
								XMLContainer->new($logger, $xml_doceid, $xml_sparql),
								"class_query",
								1,
								$query_attributes);
				my $query = ClassQuery->new($logger, $xml_object);
				$queries->add($query);
				$self->increment("NEXT_TASK1_CLASS_QUERY_NUM");
				$types_used{$query_type} = 1;
			}
		}
	}
}

sub generate_task1_graph_queries {
	my ($self, $year, $topic_id, $prevailing_theory_id) = @_;
	$self->generate_graph_queries($year, $topic_id, $prevailing_theory_id, "task1");
}

sub generate_task2_zerohop_queries {
	my ($self, $year, $topic_id, $prevailing_theory_id) = @_;
	my $logger = $self->get("LOGGER");
	my $dtd_file = $self->get("PARAMETERS")->get("DTD_FILES")->get("BY_KEY", "zerohop_query");
	my $output_dir = $self->get("PARAMETERS")->get("OUTPUT_DIR");
	system("mkdir -p $output_dir");
	my $xml_file = "$output_dir/task2_zerohop_queries.xml";
	my $queries = $self->get("TA2_ZEROHOP_QUERIES");
	if ($queries eq "nil") {
		$queries = QuerySet->new($logger, $dtd_file, $xml_file);
		$self->set("TA2_ZEROHOP_QUERIES", $queries);
	}
	my $subcontainer = $self->get("PREVAILING_THEORY_ENTRIES")->get("BY_KEY", $topic_id . "_" . $prevailing_theory_id);
	my $query_id_prefix = $self->get("PARAMETERS")->get("TA2_ZEROHOP_QUERYID_PREFIX");
	my $reference_kbid_prefix = $self->get("PARAMETERS")->get("REFERENCE_KBID_PREFIX");
	my %argument_kbids_used;
	foreach my $pt_entry($subcontainer->toarray()) {
		# Is this an entity involved in the prevailing theory?
		my $argument_kbid = $pt_entry->get("ARGUMENT_KBID");
		if($argument_kbid =~ /^\d+$/) {
			# If yes, generate the query
			next if $argument_kbids_used{$argument_kbid};
			my $i = $self->get("NEXT_TASK2_ZEROHOP_QUERY_NUM");
			my $query_id = "$query_id_prefix\_$i";
			my $query_reference_kbid = $reference_kbid_prefix . ":" . $argument_kbid;
			# Generate the XML object corresponding to the query
			my $sparql = $self->get("TA2_ZEROHOP_SPARQL_QUERY_TEMPLATE");
			$sparql =~ s/\[__QUERY_ID__\]/$query_id/gs;
			$sparql =~ s/\[__KBID__\]/$query_reference_kbid/gs;
			my $query_attributes = XMLAttributes->new($logger);
			$query_attributes->add("$query_id", "id");
			my $xml_argument_kbid = XMLElement->new($logger, $query_reference_kbid, "reference_kbid", 0);
			my $xml_sparql = XMLElement->new($logger, $sparql, "sparql", 1);
			my $xml_object = XMLElement->new($logger,
							XMLContainer->new($logger, $xml_argument_kbid, $xml_sparql),
							"zerohop_query",
							1,
							$query_attributes);
			my $query = ZeroHopQuery->new($logger, $xml_object);
			$queries->add($query);
			$self->increment("NEXT_TASK2_ZEROHOP_QUERY_NUM");
			$argument_kbids_used{$argument_kbid} = 1;
		}
	}
}

sub generate_task2_graph_queries {
	my ($self, $year, $topic_id, $prevailing_theory_id) = @_;
	$self->generate_graph_queries($year, $topic_id, $prevailing_theory_id, "task2");
}



sub get_TA1_CLASS_SPARQL_QUERY_TEMPLATE {
	my ($self) = @_;
	my $sparql = <<'END_SPARQL_QUERY';
	<![CDATA[
              PREFIX ldcOnt: <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/SeedlingOntology#>
              PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
              PREFIX aida:  <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/InterchangeOntology#>
              PREFIX cfn:   <https://verdi.nextcentury.com/custom-function/>
              PREFIX xsd:   <http://www.w3.org/2001/XMLSchema#>

              # Query: [__QUERY_ID__]
              # Query description: Find all informative mentions of type [__TYPE__]
              # Aggregate confidence of ?cluster is product of
              #       ?t_cv       # confidenceValue of asserting ?member being of ?type
              #       ?cm_cv      # confidenceValue of asserting ?member being a member of the ?cluster
              #       ?j_cv       # confidenceValue of informativeJustification

              SELECT 
                ?docid      # sourceDocument
                ?query_type # query type
                ?cluster    # ?cluster containing ?member1 of type ?type that matches ?query_type
                ?type       # matching ?type
                ?infj_span  # informativeJustification span
                ?t_cv       # confidenceValue of asserting ?member being of ?type
                ?cm_cv      # confidenceValue of asserting ?member being a member of the ?cluster
                ?j_cv       # confidenceValue of informativeJustification

              WHERE {

                  BIND(ldcOnt:[__TYPE__] as ?query_type)

                  ?cluster              aida:informativeJustification ?inf_justification .

                  ?statement1           a                             rdf:Statement .
                  ?statement1           rdf:object                    ?type .
                  ?statement1           rdf:predicate                 rdf:type .
                  ?statement1           rdf:subject                   ?member .
                  ?statement1           aida:justifiedBy              ?inf_justification .
                  ?statement1           aida:confidence               ?t_confidence .
                  ?t_confidence         aida:confidenceValue          ?t_cv .

                  FILTER(cfn:superTypeOf(str(?query_type), str(?type)))

                  ?statement2           a                             aida:ClusterMembership .
                  ?statement2           aida:cluster                  ?cluster .
                  ?statement2           aida:clusterMember            ?member .
                  ?statement2           aida:confidence               ?cm_confidence .
                  ?cm_confidence       aida:confidenceValue          ?cm_cv .

                  ?inf_justification    aida:source          ?doceid .
                  ?inf_justification    aida:sourceDocument  ?docid .
                  ?inf_justification    aida:confidence      ?j_confidence .
                  ?j_confidence         aida:confidenceValue ?j_cv .

                  OPTIONAL {
                         ?inf_justification a                           aida:TextJustification .
                         ?inf_justification aida:startOffset            ?so .
                         ?inf_justification aida:endOffsetInclusive     ?eo
                  }
                  OPTIONAL {
                         ?inf_justification a                           aida:ImageJustification .
                         ?inf_justification aida:boundingBox            ?bb  .
                         ?bb                aida:boundingBoxUpperLeftX  ?ulx .
                         ?bb                aida:boundingBoxUpperLeftY  ?uly .
                         ?bb                aida:boundingBoxLowerRightX ?lrx .
                         ?bb                aida:boundingBoxLowerRightY ?lry
                  }
                  OPTIONAL {
                         ?inf_justification a                           aida:KeyFrameVideoJustification .
                         ?inf_justification aida:keyFrame               ?kfid .
                         ?inf_justification aida:boundingBox            ?bb  .
                         ?bb                aida:boundingBoxUpperLeftX  ?ulx .
                         ?bb                aida:boundingBoxUpperLeftY  ?uly .
                         ?bb                aida:boundingBoxLowerRightX ?lrx .
                         ?bb                aida:boundingBoxLowerRightY ?lry
                  }
                  OPTIONAL {
                         ?inf_justification a                           aida:ShotVideoJustification .
                         ?inf_justification aida:shot                   ?sid
                  }
                  OPTIONAL {
                         ?inf_justification a                           aida:AudioJustification .
                         ?inf_justification aida:startTimestamp         ?st .
                         ?inf_justification aida:endTimestamp           ?et
                  }

                  BIND( IF( BOUND(?sid), ?sid, "__NULL__") AS ?_sid) .
                  BIND( IF( BOUND(?kfid), ?kfid, "__NULL__") AS ?_kfid) .
                  BIND( IF( BOUND(?so), ?so, "__NULL__") AS ?_so) .
                  BIND( IF( BOUND(?eo), ?eo, "__NULL__") AS ?_eo) .
                  BIND( IF( BOUND(?st), ?st, "__NULL__") AS ?_st) .
                  BIND( IF( BOUND(?et), ?et, "__NULL__") AS ?_et) .
                  BIND( IF( BOUND(?ulx), ?ulx, "__NULL__") AS ?_ulx) .
                  BIND( IF( BOUND(?uly), ?uly, "__NULL__") AS ?_uly) .
                  BIND( IF( BOUND(?lrx), ?lrx, "__NULL__") AS ?_lrx) .
                  BIND( IF( BOUND(?lry), ?lry, "__NULL__") AS ?_lry) .

                  BIND( cfn:getSpan(str(?docid), str(?doceid), str(?_sid), str(?_kfid), str(?_so), str(?_eo), str(?_ulx), str(?_uly), str(?_lrx), str(?_lry), str(?_st), str(?_et) ) as ?infj_span ) .
              }
	]]>
END_SPARQL_QUERY
	$sparql;
}

sub get_TA1_GRAPH_SPARQL_QUERY_TEMPLATE {
	my ($self) = @_;
	my $sparql = <<'END_SPARQL_QUERY';
	<![CDATA[
              PREFIX ldcOnt: <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/SeedlingOntology#>
              PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
              PREFIX aida:  <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/InterchangeOntology#>
              PREFIX cfn:   <https://verdi.nextcentury.com/custom-function/>
              PREFIX xsd:   <http://www.w3.org/2001/XMLSchema#>
              
              # Query: [__QUERY_ID__]
              # Query description: Find all edges of type ldcOnt:[__PREDICATE__]
              
              # By default, NIST will compute aggregate edge justification confidence (AEJC) as product of:
              #        ?oinf_j_cv    # confidence of object informativeJustification
              #        ?obcm_cv      # cluster membership confidence of the object
              #        ?edge_cv      # confidence of a compound justification for the argument assertion
              #        ?sbcm_cv      # cluster membership confidence of the subject
              
              SELECT ?docid        # sourceDocument
                     ?edge_type_q  # edge type in the query
                     ?edge_type    # edge type in response matching the edge type in query
                     ?object_cluster  ?objectmo  ?oinf_j_span # object cluster, cluster member and its informativeJustification
                     ?subject_cluster ?subjectmo  # subject cluster, cluster member (its informativeJustification is not needed by LDC for assessment)
                     ?ej_span      # CompoundJustification span(s) for argument assertion
                     ?oinf_j_cv    # confidence of object informativeJustification
                     ?obcm_cv      # cluster membership confidence of the object
                     ?edge_cv      # confidence of a compound justification for the argument assertion
                     ?sbcm_cv      # cluster membership confidence of the subject
              
              WHERE {
              
                  BIND (ldcOnt:[__PREDICATE__] as ?edge_type_q)
              
                  # Get the object informativeJustification
                  ?objectmo             a                             aida:Entity .
                  ?objectmo             aida:informativeJustification ?oinf_justification .
                  ?oinf_justification   aida:sourceDocument           ?docid .
                  ?oinf_justification   aida:source                   ?oinf_j_doceid .
                  ?oinf_justification   aida:confidence               ?oinf_j_confidence .
                  ?oinf_j_confidence    aida:confidenceValue          ?oinf_j_cv .
              
                  # Get the object cluster and cluster membership confidence
                  ?statement1           a                             aida:ClusterMembership .
                  ?statement1           aida:cluster                  ?object_cluster .
                  ?statement1           aida:clusterMember            ?objectmo .
                  ?statement1           aida:confidence               ?objcm_confidence .
                  ?objcm_confidence     aida:confidenceValue          ?obcm_cv .
              
                  # Get the edge and it's justifications
                  ?statement2           rdf:object                    ?objectmo .
                  ?statement2           rdf:predicate                 ?edge_type .
                  ?statement2           rdf:subject                   ?subjectmo .
              
                  # The ?edge_type should be matching ?edge_type_q
                  FILTER(cfn:superTypeOf(str(?edge_type_q), str(?edge_type)))
              
                  ?statement2           aida:justifiedBy              ?compoundedge_just .
                  ?statement2           aida:confidence               ?edge_confidence .
                  ?edge_confidence      aida:confidenceValue          ?edge_cv .
                  # The first contained justification
                  ?compoundedge_just    aida:containedJustification   ?edge_justification1 .
                  ?edge_justification1  aida:sourceDocument           ?docid .
                  ?edge_justification1  aida:source                   ?edgecj1_doceid .
                  ?edge_justification1  aida:confidence               ?edgecj1_j_confidence .
                  ?edgecj1_j_confidence aida:confidenceValue          ?edgecj1_j_cv .
                  # The second contained justification
                  ?compoundedge_just    aida:containedJustification   ?edge_justification2 .
                  ?edge_justification2  aida:sourceDocument           ?docid .
                  ?edge_justification2  aida:source                   ?edgecj2_doceid .
                  ?edge_justification2  aida:confidence               ?edgecj2_j_confidence .
                  ?edgecj2_j_confidence aida:confidenceValue          ?edgecj2_j_cv .
              
                  # Get the subject informativeJustification
                  ?subjectmo            aida:informativeJustification ?sinf_justification .
                  ?sinf_justification   aida:sourceDocument           ?docid .
                  ?sinf_justification   aida:source                   ?sinf_j_doceid .
                  ?sinf_justification   aida:confidence               ?sinf_j_confidence .
                  ?sinf_j_confidence    aida:confidenceValue          ?sinf_j_cv .
              
                  # Get the subject cluster and cluster membership confidence
                  ?statement3           a                             aida:ClusterMembership .
                  ?statement3           aida:cluster                  ?subject_cluster .
                  ?statement3           aida:clusterMember            ?subjectmo .
                  ?statement3           aida:confidence               ?subjcm_confidence .
                  ?subjcm_confidence    aida:confidenceValue          ?sbcm_cv .
              
                  # Get the number of justifications (?edge_num_cjs) that are contained in
                  # the ?compoundedge_just
                  {
                     SELECT ?compoundedge_just (count(?cj) as ?edge_num_cjs)
                     WHERE {
                         ?compoundedge_just aida:containedJustification ?cj .
                     }
                     GROUP BY ?compoundedge_just
                  }
              
                  # Get object's informative justification span
                  OPTIONAL {
                         ?oinf_justification a                           aida:TextJustification .
                         ?oinf_justification aida:startOffset            ?oso .
                         ?oinf_justification aida:endOffsetInclusive     ?oeo
                  }
                  OPTIONAL {
                         ?oinf_justification a                           aida:ImageJustification .
                         ?oinf_justification aida:boundingBox            ?obb  .
                         ?obb                aida:boundingBoxUpperLeftX  ?oulx .
                         ?obb                aida:boundingBoxUpperLeftY  ?ouly .
                         ?obb                aida:boundingBoxLowerRightX ?olrx .
                         ?obb                aida:boundingBoxLowerRightY ?olry
                  }
                  OPTIONAL {
                         ?oinf_justification a                           aida:KeyFrameVideoJustification .
                         ?oinf_justification aida:keyFrame               ?okfid .
                         ?oinf_justification aida:boundingBox            ?obb  .
                         ?obb                aida:boundingBoxUpperLeftX  ?oulx .
                         ?obb                aida:boundingBoxUpperLeftY  ?ouly .
                         ?obb                aida:boundingBoxLowerRightX ?olrx .
                         ?obb                aida:boundingBoxLowerRightY ?olry
                  }
                  OPTIONAL {
                         ?oinf_justification a                           aida:ShotVideoJustification .
                         ?oinf_justification aida:shot                   ?osid
                  }
                  OPTIONAL {
                         ?oinf_justification a                           aida:AudioJustification .
                         ?oinf_justification aida:startTimestamp         ?ost .
                         ?oinf_justification aida:endTimestamp           ?oet
                  }
              
                  BIND( IF( BOUND(?osid), ?osid, "__NULL__") AS ?_osid) .
                  BIND( IF( BOUND(?okfid), ?okfid, "__NULL__") AS ?_okfid) .
                  BIND( IF( BOUND(?oso), ?oso, "__NULL__") AS ?_oso) .
                  BIND( IF( BOUND(?oeo), ?oeo, "__NULL__") AS ?_oeo) .
                  BIND( IF( BOUND(?ost), ?ost, "__NULL__") AS ?_ost) .
                  BIND( IF( BOUND(?oet), ?oet, "__NULL__") AS ?_oet) .
                  BIND( IF( BOUND(?oulx), ?oulx, "__NULL__") AS ?_oulx) .
                  BIND( IF( BOUND(?ouly), ?ouly, "__NULL__") AS ?_ouly) .
                  BIND( IF( BOUND(?olrx), ?olrx, "__NULL__") AS ?_olrx) .
                  BIND( IF( BOUND(?olry), ?olry, "__NULL__") AS ?_olry) .
              
                  BIND( cfn:getSpan(str(?docid), str(?oinf_j_doceid), str(?_osid), str(?_okfid), str(?_oso), str(?_oeo), str(?_oulx), str(?_ouly), str(?_olrx), str(?_olry), str(?_ost), str(?_oet) ) as ?oinf_j_span ) .
              
                  # Get subject's informative justification span
                  OPTIONAL {
                         ?sinf_justification a                           aida:TextJustification .
                         ?sinf_justification aida:startOffset            ?sso .
                         ?sinf_justification aida:endOffsetInclusive     ?seo
                  }
                  OPTIONAL {
                         ?sinf_justification a                           aida:ImageJustification .
                         ?sinf_justification aida:boundingBox            ?sbb  .
                         ?sbb                aida:boundingBoxUpperLeftX  ?sulx .
                         ?sbb                aida:boundingBoxUpperLeftY  ?suly .
                         ?sbb                aida:boundingBoxLowerRightX ?slrx .
                         ?sbb                aida:boundingBoxLowerRightY ?slry
                  }
                  OPTIONAL {
                         ?sinf_justification a                           aida:KeyFrameVideoJustification .
                         ?sinf_justification aida:keyFrame               ?skfid .
                         ?sinf_justification aida:boundingBox            ?sbb  .
                         ?sbb                aida:boundingBoxUpperLeftX  ?sulx .
                         ?sbb                aida:boundingBoxUpperLeftY  ?suly .
                         ?sbb                aida:boundingBoxLowerRightX ?slrx .
                         ?sbb                aida:boundingBoxLowerRightY ?slry
                  }
                  OPTIONAL {
                         ?sinf_justification a                           aida:ShotVideoJustification .
                         ?sinf_justification aida:shot                   ?ssid
                  }
                  OPTIONAL {
                         ?sinf_justification a                           aida:AudioJustification .
                         ?sinf_justification aida:startTimestamp         ?sst .
                         ?sinf_justification aida:endTimestamp           ?set
                  }
              
                  BIND( IF( BOUND(?ssid), ?ssid, "__NULL__") AS ?_ssid) .
                  BIND( IF( BOUND(?skfid), ?skfid, "__NULL__") AS ?_skfid) .
                  BIND( IF( BOUND(?sso), ?sso, "__NULL__") AS ?_sso) .
                  BIND( IF( BOUND(?seo), ?seo, "__NULL__") AS ?_seo) .
                  BIND( IF( BOUND(?sst), ?sst, "__NULL__") AS ?_sst) .
                  BIND( IF( BOUND(?set), ?set, "__NULL__") AS ?_set) .
                  BIND( IF( BOUND(?sulx), ?sulx, "__NULL__") AS ?_sulx) .
                  BIND( IF( BOUND(?suly), ?suly, "__NULL__") AS ?_suly) .
                  BIND( IF( BOUND(?slrx), ?slrx, "__NULL__") AS ?_slrx) .
                  BIND( IF( BOUND(?slry), ?slry, "__NULL__") AS ?_slry) .
              
                  BIND( cfn:getSpan(str(?docid), str(?sinf_j_doceid), str(?_ssid), str(?_skfid), str(?_sso), str(?_seo), str(?_sulx), str(?_suly), str(?_slrx), str(?_slry), str(?_sst), str(?_set) ) as ?sinf_j_span ) .
              
                  # Get edge's justification span # 1
                  OPTIONAL {
                         ?edge_justification1 a                           aida:TextJustification .
                         ?edge_justification1 aida:startOffset            ?ej1so .
                         ?edge_justification1 aida:endOffsetInclusive     ?ej1eo
                  }
                  OPTIONAL {
                         ?edge_justification1 a                           aida:ImageJustification .
                         ?edge_justification1 aida:boundingBox            ?ej1bb  .
                         ?ej1bb                aida:boundingBoxUpperLeftX  ?ej1ulx .
                         ?ej1bb                aida:boundingBoxUpperLeftY  ?ej1uly .
                         ?ej1bb                aida:boundingBoxLowerRightX ?ej1lrx .
                         ?ej1bb                aida:boundingBoxLowerRightY ?ej1lry
                  }
                  OPTIONAL {
                         ?edge_justification1 a                           aida:KeyFrameVideoJustification .
                         ?edge_justification1 aida:keyFrame               ?ej1kfid .
                         ?edge_justification1 aida:boundingBox            ?ej1bb  .
                         ?ej1bb                aida:boundingBoxUpperLeftX  ?ej1ulx .
                         ?ej1bb                aida:boundingBoxUpperLeftY  ?ej1uly .
                         ?ej1bb                aida:boundingBoxLowerRightX ?ej1lrx .
                         ?ej1bb                aida:boundingBoxLowerRightY ?ej1lry
                  }
                  OPTIONAL {
                         ?edge_justification1 a                           aida:ShotVideoJustification .
                         ?edge_justification1 aida:shot                   ?ej1sid
                  }
                  OPTIONAL {
                         ?edge_justification1 a                           aida:AudioJustification .
                         ?edge_justification1 aida:startTimestamp         ?ej1st .
                         ?edge_justification1 aida:endTimestamp           ?ej1et
                  }
              
                  BIND( IF( BOUND(?ej1sid), ?ej1sid, "__NULL__") AS ?_ej1sid) .
                  BIND( IF( BOUND(?ej1kfid), ?ej1kfid, "__NULL__") AS ?_ej1kfid) .
                  BIND( IF( BOUND(?ej1so), ?ej1so, "__NULL__") AS ?_ej1so) .
                  BIND( IF( BOUND(?ej1eo), ?ej1eo, "__NULL__") AS ?_ej1eo) .
                  BIND( IF( BOUND(?ej1st), ?ej1st, "__NULL__") AS ?_ej1st) .
                  BIND( IF( BOUND(?ej1et), ?ej1et, "__NULL__") AS ?_ej1et) .
                  BIND( IF( BOUND(?ej1ulx), ?ej1ulx, "__NULL__") AS ?_ej1ulx) .
                  BIND( IF( BOUND(?ej1uly), ?ej1uly, "__NULL__") AS ?_ej1uly) .
                  BIND( IF( BOUND(?ej1lrx), ?ej1lrx, "__NULL__") AS ?_ej1lrx) .
                  BIND( IF( BOUND(?ej1lry), ?ej1lry, "__NULL__") AS ?_ej1lry) .
              
                  BIND( cfn:getSpan(str(?docid), str(?edgecj1_doceid), str(?_ej1sid), str(?_ej1kfid), str(?_ej1so), str(?_ej1eo), str(?_ej1ulx), str(?_ej1uly), str(?_ej1lrx), str(?_ej1lry), str(?_ej1st), str(?_ej1et) ) as ?ej1_span ) .
              
              
                  # Get edge's justification span # 2
                  OPTIONAL {
                         ?edge_justification2 a                           aida:TextJustification .
                         ?edge_justification2 aida:startOffset            ?ej2so .
                         ?edge_justification2 aida:endOffsetInclusive     ?ej2eo
                  }
                  OPTIONAL {
                         ?edge_justification2 a                           aida:ImageJustification .
                         ?edge_justification2 aida:boundingBox            ?ej2bb  .
                         ?ej2bb               aida:boundingBoxUpperLeftX  ?ej2ulx .
                         ?ej2bb               aida:boundingBoxUpperLeftY  ?ej2uly .
                         ?ej2bb               aida:boundingBoxLowerRightX ?ej2lrx .
                         ?ej2bb               aida:boundingBoxLowerRightY ?ej2lry
                  }
                  OPTIONAL {
                         ?edge_justification2 a                           aida:KeyFrameVideoJustification .
                         ?edge_justification2 aida:keyFrame               ?ej2kfid .
                         ?edge_justification2 aida:boundingBox            ?ej2bb  .
                         ?ej2bb               aida:boundingBoxUpperLeftX  ?ej2ulx .
                         ?ej2bb               aida:boundingBoxUpperLeftY  ?ej2uly .
                         ?ej2bb               aida:boundingBoxLowerRightX ?ej2lrx .
                         ?ej2bb               aida:boundingBoxLowerRightY ?ej2lry
                  }
                  OPTIONAL {
                         ?edge_justification2 a                           aida:ShotVideoJustification .
                         ?edge_justification2 aida:shot                   ?ej2sid
                  }
                  OPTIONAL {
                         ?edge_justification2 a                           aida:AudioJustification .
                         ?edge_justification2 aida:startTimestamp         ?ej2st .
                         ?edge_justification2 aida:endTimestamp           ?ej2et
                  }
              
                  BIND( IF( BOUND(?ej2sid), ?ej2sid, "__NULL__") AS ?_ej2sid) .
                  BIND( IF( BOUND(?ej2kfid), ?ej2kfid, "__NULL__") AS ?_ej2kfid) .
                  BIND( IF( BOUND(?ej2so), ?ej2so, "__NULL__") AS ?_ej2so) .
                  BIND( IF( BOUND(?ej2eo), ?ej2eo, "__NULL__") AS ?_ej2eo) .
                  BIND( IF( BOUND(?ej2st), ?ej2st, "__NULL__") AS ?_ej2st) .
                  BIND( IF( BOUND(?ej2et), ?ej2et, "__NULL__") AS ?_ej2et) .
                  BIND( IF( BOUND(?ej2ulx), ?ej2ulx, "__NULL__") AS ?_ej2ulx) .
                  BIND( IF( BOUND(?ej2uly), ?ej2uly, "__NULL__") AS ?_ej2uly) .
                  BIND( IF( BOUND(?ej2lrx), ?ej2lrx, "__NULL__") AS ?_ej2lrx) .
                  BIND( IF( BOUND(?ej2lry), ?ej2lry, "__NULL__") AS ?_ej2lry) .
              
                  BIND( cfn:getSpan(str(?docid), str(?edgecj2_doceid), str(?_ej2sid), str(?_ej2kfid), str(?_ej2so), str(?_ej2eo), str(?_ej2ulx), str(?_ej2uly), str(?_ej2lrx), str(?_ej2lry), str(?_ej2st), str(?_ej2et) ) as ?ej2_span ) .
                  BIND(IF(?edge_num_cjs = 1, "", ?ej2_span) as ?ej2_span)
                  FILTER(?ej1_span > ?ej2_span)
                  BIND(IF(?edge_num_cjs = 1, ?ej1_span, CONCAT(CONCAT(?ej2_span,","),?ej1_span)) as ?ej_span)
              }
	]]>
END_SPARQL_QUERY
	$sparql;
}

sub get_TA2_ZEROHOP_SPARQL_QUERY_TEMPLATE {
	my ($self) = @_;
	my $sparql = <<'END_SPARQL_QUERY';
	<![CDATA[
              PREFIX ldcOnt: <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/SeedlingOntology#>
              PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
              PREFIX aida:  <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/InterchangeOntology#>
              PREFIX cfn:   <https://verdi.nextcentury.com/custom-function/>
              PREFIX xsd:   <http://www.w3.org/2001/XMLSchema#>
              
              # Query: [__QUERY_ID__]
              # Query description: Find all informative mentions of entities linked to "[__KBID__]"
              # NIST default aggregate confidence of ?cluster is a function of
              #      ?link_cv      # confidenceValue of asserting that ?cluster is the same as reference KB node ?link_target
              #      ?j_cv         # confidenceValue of informativeJustification
              
              # ?j_cv is used to rank informative mentions within a cluster for purposes of pooling and AP scoring.
              
              # In M18, we use the ?j_cv (confidence in the justification, e.g., confidence of _:b02) and interpret that confidence
              # as the confidence of linking the justification to the cluster; _:b02 is used *only* to represent an informative
              # mention for some cluster, even though that cluster is not referenced in _:b02. Ideally (in future), there would be
              # an aida:InformativeJustificationAssertion construct (paralleling the structure of an aida:LinkAssertion) that
              # associates a confidence to each aida:informativeJustification, and could represent the confidence of linking an
              # InformativeJustification to a cluster.
              
              # _:b12 a                        aida:TextJustification ;
              #      aida:confidence          [ a                     aida:Confidence ;
              #                                 aida:confidenceValue  "1.0"^^<http://www.w3.org/2001/XMLSchema#double> ;
              #                                 aida:system           ldc:testSystem
              #                               ] ;
              #      aida:endOffsetInclusive  "286"^^<http://www.w3.org/2001/XMLSchema#int> ;
              #      aida:privateData         [ a                 aida:PrivateData ;
              #                                 aida:jsonContent  "{\"mention\":\"M000721\"}" ;
              #                                 aida:system       ldc:testSystem
              #                               ] ;
              #      aida:source              "DE005" ;
              #      aida:sourceDocument      "D0100" ;
              #      aida:startOffset         "260"^^<http://www.w3.org/2001/XMLSchema#int> ;
              #      aida:system              ldc:testSystem .
              #
              # _:b11 a              aida:LinkAssertion ;
              #      aida:confidence [ a                     aida:Confidence ;
              #                        aida:confidenceValue  "0.498"^^xsd:double ;
              #                        aida:system           ldc:testSystem
              #                      ] ;
              #      aida:linkTarget "ldc:E0137" ;
              #      aida:system     ldc:testSystem .
              #
              # _:c12 a               aida:InformativeJustificationAssertion ;
              #       aida:confidence [ a                     aida:Confidence ;
              #                         aida:confidenceValue  "0.498"^^xsd:double ;
              #                         aida:system           ldc:testSystem
              #                       ] ;
              #      aida:informativeJustification _:b12 ;
              #      aida:system     ldc:testSystem .
              #
              # ldc:cluster-E0137     a                             aida:SameAsCluster ;
              #                       aida:informativeJustification _:c12 ;
              #                       aida:link                     _:b11 ;
              #                       aida:system                   ldc:testSystem .
              
              
              SELECT ?docid        # sourceDocument
                     ?link_target  # link target as part of the query
                     ?cluster      # the ?cluster linked to ?link_target
                     ?infj_span    # informativeJustification span taken from the ?cluster
                     ?j_cv         # confidenceValue of informativeJustification
                     ?link_target  # query reference KB node linked to a ?cluster
                     ?link_cv      # confidenceValue of asserting that ?cluster is the same as reference KB node ?link_target
              
              WHERE {
                  BIND ("[__KBID__]" AS ?link_target)
              
                  # Find ?cluster linked to "[__KBID__]"
                  # Find the ?link_cv: confidenceValue of linking to external KB entity
                  ?cluster              a                             aida:SameAsCluster .
                  ?cluster              aida:informativeJustification ?inf_justification .
                  ?cluster              aida:link                     ?ref_kb_link .
                  ?ref_kb_link          a                             aida:LinkAssertion .
                  ?ref_kb_link          aida:linkTarget               ?link_target .
                  ?ref_kb_link          aida:confidence               ?link_confidence .
                  ?link_confidence      aida:confidenceValue          ?link_cv .
              
                  # Find mention spans for ?inf_justification
                  ?inf_justification    aida:source          ?doceid .
                  ?inf_justification    aida:sourceDocument  ?docid .
                  ?inf_justification    aida:confidence      ?j_confidence .
                  ?j_confidence         aida:confidenceValue ?j_cv .
              
                  OPTIONAL {
                         ?inf_justification a                           aida:TextJustification .
                         ?inf_justification aida:startOffset            ?so .
                         ?inf_justification aida:endOffsetInclusive     ?eo
                  }
                  OPTIONAL {
                         ?inf_justification a                           aida:ImageJustification .
                         ?inf_justification aida:boundingBox            ?bb  .
                         ?bb                aida:boundingBoxUpperLeftX  ?ulx .
                         ?bb                aida:boundingBoxUpperLeftY  ?uly .
                         ?bb                aida:boundingBoxLowerRightX ?lrx .
                         ?bb                aida:boundingBoxLowerRightY ?lry
                  }
                  OPTIONAL {
                         ?inf_justification a                           aida:KeyFrameVideoJustification .
                         ?inf_justification aida:keyFrame               ?kfid .
                         ?inf_justification aida:boundingBox            ?bb  .
                         ?bb                aida:boundingBoxUpperLeftX  ?ulx .
                         ?bb                aida:boundingBoxUpperLeftY  ?uly .
                         ?bb                aida:boundingBoxLowerRightX ?lrx .
                         ?bb                aida:boundingBoxLowerRightY ?lry
                  }
                  OPTIONAL {
                         ?inf_justification a                           aida:ShotVideoJustification .
                         ?inf_justification aida:shot                   ?sid
                  }
                  OPTIONAL {
                         ?inf_justification a                           aida:AudioJustification .
                         ?inf_justification aida:startTimestamp         ?st .
                         ?inf_justification aida:endTimestamp           ?et
                  }
              
                  BIND( IF( BOUND(?sid), ?sid, "__NULL__") AS ?_sid) .
                  BIND( IF( BOUND(?kfid), ?kfid, "__NULL__") AS ?_kfid) .
                  BIND( IF( BOUND(?so), ?so, "__NULL__") AS ?_so) .
                  BIND( IF( BOUND(?eo), ?eo, "__NULL__") AS ?_eo) .
                  BIND( IF( BOUND(?st), ?st, "__NULL__") AS ?_st) .
                  BIND( IF( BOUND(?et), ?et, "__NULL__") AS ?_et) .
                  BIND( IF( BOUND(?ulx), ?ulx, "__NULL__") AS ?_ulx) .
                  BIND( IF( BOUND(?uly), ?uly, "__NULL__") AS ?_uly) .
                  BIND( IF( BOUND(?lrx), ?lrx, "__NULL__") AS ?_lrx) .
                  BIND( IF( BOUND(?lry), ?lry, "__NULL__") AS ?_lry) .
              
                  BIND( cfn:getSpan(str(?docid), str(?doceid), str(?_sid), str(?_kfid), str(?_so), str(?_eo), str(?_ulx), str(?_uly), str(?_lrx), str(?_lry), str(?_st), str(?_et) ) as ?infj_span ) .
              }
	]]>
END_SPARQL_QUERY
	$sparql;
}

sub get_TA2_GRAPH_SPARQL_QUERY_TEMPLATE {
	my ($self) = @_;
	my $sparql = <<'END_SPARQL_QUERY';
	<![CDATA[
              PREFIX ldcOnt: <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/SeedlingOntology#>
              PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
              PREFIX aida:  <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/InterchangeOntology#>
              PREFIX cfn:   <https://verdi.nextcentury.com/custom-function/>
              PREFIX xsd:   <http://www.w3.org/2001/XMLSchema#>
              
              # Query: [__QUERY_ID__]
              # Query description: Find all edges of type ldcOnt:Conflict.Attack_Place such that the object
              #                    of the edge is linked to reference KB node [__KBID__]
              #
              # Edge: consists of a Subject (cluster) Id, a Predicate label and an Object (cluster) Id. Subject is an event
              # KE (cluster) or relation KE (cluster). Object is an entity KE (cluster), relation KE (cluster), or event KE (cluster).
              # An edge that is returned in response to a TA2 graph query will only have entity KEs as the Object (because the 
              # TA2 graph query will bind the Object to a specific entity in the evaluation reference KB).
              #
              # Aggregate edge justification confidence (AEJC) is used to rank triples to determine which will be pooled and assessed by LDC.
              # AEJC is also used to rank edges whose triples will be assessed by LDC.
              # AEJC is also used to compute subject importance, to determine which relation and event frames get assessed by LDC.
              #
              # By default, NIST will compute aggregate edge justification confidence (AEJC) for TA2 as the product of:
              #        ?orfkblink_cv # confidence of linking the object to the query reference KB ID
              #        ?oinf_j_cv    # confidence of object informativeJustification
              #        ?obcm_cv      # cluster membership confidence of the object
              #        ?edge_cv      # confidence of a compound justification for the argument assertion
              #        ?sbcm_cv      # cluster membership confidence of the subject
              
              SELECT ?docid        # sourceDocument
                     ?edge_type_q  # edge type in the query
                     ?edge_type    # edge type in response matching the edge type in query
                     ?olink_target # reference KB node linked to the object of the edge
                     ?object_cluster  ?objectmo  ?oinf_j_span # object cluster, cluster member and its informativeJustification
                     ?subject_cluster ?subjectmo  # subject cluster, cluster member (its informativeJustification is not needed by LDC for assessment)
                     ?ej_span      # CompoundJustification span(s) for argument assertion
                     ?orfkblink_cv # confidence of linking the object to the query reference KB ID
                     ?oinf_j_cv    # confidence of object informativeJustification
                     ?obcm_cv      # cluster membership confidence of the object
                     ?edge_cv      # confidence of a compound justification for the argument assertion
                     ?sbcm_cv      # cluster membership confidence of the subject
              
              WHERE {
              
                  BIND ("[__KBID__]" AS ?olink_target)
                  BIND (ldcOnt:[__PREDICATE__] as ?edge_type_q)
              
                  # Find ?objectmo linked to "[__KBID__]"
                  ?objectmo             a                             aida:Entity .
                  ?objectmo             aida:link                     ?objectmo_rfkbl .
              
                  ?objectmo_rfkbl       a                             aida:LinkAssertion .
                  ?objectmo_rfkbl       aida:linkTarget               ?olink_target .
                  ?objectmo_rfkbl       aida:confidence               ?orfkblink_confidence .
                  ?orfkblink_confidence aida:confidenceValue          ?orfkblink_cv .
              
                  # Get the object informativeJustification
                  ?objectmo             aida:informativeJustification ?oinf_justification .
                  ?oinf_justification   aida:sourceDocument           ?docid .
                  ?oinf_justification   aida:source                   ?oinf_j_doceid .
                  ?oinf_justification   aida:confidence               ?oinf_j_confidence .
                  ?oinf_j_confidence    aida:confidenceValue          ?oinf_j_cv .
              
                  # Get the object cluster and cluster membership confidence
                  ?statement1           a                             aida:ClusterMembership .
                  ?statement1           aida:cluster                  ?object_cluster .
                  ?statement1           aida:clusterMember            ?objectmo .
                  ?statement1           aida:confidence               ?objcm_confidence .
                  ?objcm_confidence     aida:confidenceValue          ?obcm_cv .
              
                  # Get the edge and it's justifications
                  ?statement2           rdf:object                    ?objectmo .
                  ?statement2           rdf:predicate                 ?edge_type .
                  ?statement2           rdf:subject                   ?subjectmo .
              
                  # The ?edge_type should be matching ?edge_type_q
                  FILTER(cfn:superTypeOf(str(?edge_type_q), str(?edge_type)))
              
                  ?statement2           aida:justifiedBy              ?compoundedge_just .
                  ?statement2           aida:confidence               ?edge_confidence .
                  ?edge_confidence      aida:confidenceValue          ?edge_cv .
                  # The first contained justification
                  ?compoundedge_just    aida:containedJustification   ?edge_justification1 .
                  ?edge_justification1  aida:sourceDocument           ?docid .
                  ?edge_justification1  aida:source                   ?edgecj1_doceid .
                  ?edge_justification1  aida:confidence               ?edgecj1_j_confidence .
                  ?edgecj1_j_confidence aida:confidenceValue          ?edgecj1_j_cv .
                  # The second contained justification
                  ?compoundedge_just    aida:containedJustification   ?edge_justification2 .
                  ?edge_justification2  aida:sourceDocument           ?docid .
                  ?edge_justification2  aida:source                   ?edgecj2_doceid .
                  ?edge_justification2  aida:confidence               ?edgecj2_j_confidence .
                  ?edgecj2_j_confidence aida:confidenceValue          ?edgecj2_j_cv .
              
                  # Get the subject informativeJustification
                  ?subjectmo            aida:informativeJustification ?sinf_justification .
                  ?sinf_justification   aida:sourceDocument           ?docid .
                  ?sinf_justification   aida:source                   ?sinf_j_doceid .
                  ?sinf_justification   aida:confidence               ?sinf_j_confidence .
                  ?sinf_j_confidence    aida:confidenceValue          ?sinf_j_cv .
              
                  # Get the subject cluster and cluster membership confidence
                  ?statement3           a                             aida:ClusterMembership .
                  ?statement3           aida:cluster                  ?subject_cluster .
                  ?statement3           aida:clusterMember            ?subjectmo .
                  ?statement3           aida:confidence               ?subjcm_confidence .
                  ?subjcm_confidence    aida:confidenceValue          ?sbcm_cv .
              
                  # Get the number of justifications (?edge_num_cjs) that are contained in
                  # the ?compoundedge_just
                  {
                     SELECT ?compoundedge_just (count(?cj) as ?edge_num_cjs)
                     WHERE {
                         ?compoundedge_just aida:containedJustification ?cj .
                     }
                     GROUP BY ?compoundedge_just
                  }
              
                  # Get object's informative justification span
                  OPTIONAL {
                         ?oinf_justification a                           aida:TextJustification .
                         ?oinf_justification aida:startOffset            ?oso .
                         ?oinf_justification aida:endOffsetInclusive     ?oeo
                  }
                  OPTIONAL {
                         ?oinf_justification a                           aida:ImageJustification .
                         ?oinf_justification aida:boundingBox            ?obb  .
                         ?obb                aida:boundingBoxUpperLeftX  ?oulx .
                         ?obb                aida:boundingBoxUpperLeftY  ?ouly .
                         ?obb                aida:boundingBoxLowerRightX ?olrx .
                         ?obb                aida:boundingBoxLowerRightY ?olry
                  }
                  OPTIONAL {
                         ?oinf_justification a                           aida:KeyFrameVideoJustification .
                         ?oinf_justification aida:keyFrame               ?okfid .
                         ?oinf_justification aida:boundingBox            ?obb  .
                         ?obb                aida:boundingBoxUpperLeftX  ?oulx .
                         ?obb                aida:boundingBoxUpperLeftY  ?ouly .
                         ?obb                aida:boundingBoxLowerRightX ?olrx .
                         ?obb                aida:boundingBoxLowerRightY ?olry
                  }
                  OPTIONAL {
                         ?oinf_justification a                           aida:ShotVideoJustification .
                         ?oinf_justification aida:shot                   ?osid
                  }
                  OPTIONAL {
                         ?oinf_justification a                           aida:AudioJustification .
                         ?oinf_justification aida:startTimestamp         ?ost .
                         ?oinf_justification aida:endTimestamp           ?oet
                  }
              
                  BIND( IF( BOUND(?osid), ?osid, "__NULL__") AS ?_osid) .
                  BIND( IF( BOUND(?okfid), ?okfid, "__NULL__") AS ?_okfid) .
                  BIND( IF( BOUND(?oso), ?oso, "__NULL__") AS ?_oso) .
                  BIND( IF( BOUND(?oeo), ?oeo, "__NULL__") AS ?_oeo) .
                  BIND( IF( BOUND(?ost), ?ost, "__NULL__") AS ?_ost) .
                  BIND( IF( BOUND(?oet), ?oet, "__NULL__") AS ?_oet) .
                  BIND( IF( BOUND(?oulx), ?oulx, "__NULL__") AS ?_oulx) .
                  BIND( IF( BOUND(?ouly), ?ouly, "__NULL__") AS ?_ouly) .
                  BIND( IF( BOUND(?olrx), ?olrx, "__NULL__") AS ?_olrx) .
                  BIND( IF( BOUND(?olry), ?olry, "__NULL__") AS ?_olry) .
              
                  BIND( cfn:getSpan(str(?docid), str(?oinf_j_doceid), str(?_osid), str(?_okfid), str(?_oso), str(?_oeo), str(?_oulx), str(?_ouly), str(?_olrx), str(?_olry), str(?_ost), str(?_oet) ) as ?oinf_j_span ) .
              
                  # Get subject's informative justification span
                  OPTIONAL {
                         ?sinf_justification a                           aida:TextJustification .
                         ?sinf_justification aida:startOffset            ?sso .
                         ?sinf_justification aida:endOffsetInclusive     ?seo
                  }
                  OPTIONAL {
                         ?sinf_justification a                           aida:ImageJustification .
                         ?sinf_justification aida:boundingBox            ?sbb  .
                         ?sbb                aida:boundingBoxUpperLeftX  ?sulx .
                         ?sbb                aida:boundingBoxUpperLeftY  ?suly .
                         ?sbb                aida:boundingBoxLowerRightX ?slrx .
                         ?sbb                aida:boundingBoxLowerRightY ?slry
                  }
                  OPTIONAL {
                         ?sinf_justification a                           aida:KeyFrameVideoJustification .
                         ?sinf_justification aida:keyFrame               ?skfid .
                         ?sinf_justification aida:boundingBox            ?sbb  .
                         ?sbb                aida:boundingBoxUpperLeftX  ?sulx .
                         ?sbb                aida:boundingBoxUpperLeftY  ?suly .
                         ?sbb                aida:boundingBoxLowerRightX ?slrx .
                         ?sbb                aida:boundingBoxLowerRightY ?slry
                  }
                  OPTIONAL {
                         ?sinf_justification a                           aida:ShotVideoJustification .
                         ?sinf_justification aida:shot                   ?ssid
                  }
                  OPTIONAL {
                         ?sinf_justification a                           aida:AudioJustification .
                         ?sinf_justification aida:startTimestamp         ?sst .
                         ?sinf_justification aida:endTimestamp           ?set
                  }
              
                  BIND( IF( BOUND(?ssid), ?ssid, "__NULL__") AS ?_ssid) .
                  BIND( IF( BOUND(?skfid), ?skfid, "__NULL__") AS ?_skfid) .
                  BIND( IF( BOUND(?sso), ?sso, "__NULL__") AS ?_sso) .
                  BIND( IF( BOUND(?seo), ?seo, "__NULL__") AS ?_seo) .
                  BIND( IF( BOUND(?sst), ?sst, "__NULL__") AS ?_sst) .
                  BIND( IF( BOUND(?set), ?set, "__NULL__") AS ?_set) .
                  BIND( IF( BOUND(?sulx), ?sulx, "__NULL__") AS ?_sulx) .
                  BIND( IF( BOUND(?suly), ?suly, "__NULL__") AS ?_suly) .
                  BIND( IF( BOUND(?slrx), ?slrx, "__NULL__") AS ?_slrx) .
                  BIND( IF( BOUND(?slry), ?slry, "__NULL__") AS ?_slry) .
              
                  BIND( cfn:getSpan(str(?docid), str(?sinf_j_doceid), str(?_ssid), str(?_skfid), str(?_sso), str(?_seo), str(?_sulx), str(?_suly), str(?_slrx), str(?_slry), str(?_sst), str(?_set) ) as ?sinf_j_span ) .
              
                  # Get edge's justification span # 1
                  OPTIONAL {
                         ?edge_justification1 a                           aida:TextJustification .
                         ?edge_justification1 aida:startOffset            ?ej1so .
                         ?edge_justification1 aida:endOffsetInclusive     ?ej1eo
                  }
                  OPTIONAL {
                         ?edge_justification1 a                           aida:ImageJustification .
                         ?edge_justification1 aida:boundingBox            ?ej1bb  .
                         ?ej1bb                aida:boundingBoxUpperLeftX  ?ej1ulx .
                         ?ej1bb                aida:boundingBoxUpperLeftY  ?ej1uly .
                         ?ej1bb                aida:boundingBoxLowerRightX ?ej1lrx .
                         ?ej1bb                aida:boundingBoxLowerRightY ?ej1lry
                  }
                  OPTIONAL {
                         ?edge_justification1 a                           aida:KeyFrameVideoJustification .
                         ?edge_justification1 aida:keyFrame               ?ej1kfid .
                         ?edge_justification1 aida:boundingBox            ?ej1bb  .
                         ?ej1bb                aida:boundingBoxUpperLeftX  ?ej1ulx .
                         ?ej1bb                aida:boundingBoxUpperLeftY  ?ej1uly .
                         ?ej1bb                aida:boundingBoxLowerRightX ?ej1lrx .
                         ?ej1bb                aida:boundingBoxLowerRightY ?ej1lry
                  }
                  OPTIONAL {
                         ?edge_justification1 a                           aida:ShotVideoJustification .
                         ?edge_justification1 aida:shot                   ?ej1sid
                  }
                  OPTIONAL {
                         ?edge_justification1 a                           aida:AudioJustification .
                         ?edge_justification1 aida:startTimestamp         ?ej1st .
                         ?edge_justification1 aida:endTimestamp           ?ej1et
                  }
              
                  BIND( IF( BOUND(?ej1sid), ?ej1sid, "__NULL__") AS ?_ej1sid) .
                  BIND( IF( BOUND(?ej1kfid), ?ej1kfid, "__NULL__") AS ?_ej1kfid) .
                  BIND( IF( BOUND(?ej1so), ?ej1so, "__NULL__") AS ?_ej1so) .
                  BIND( IF( BOUND(?ej1eo), ?ej1eo, "__NULL__") AS ?_ej1eo) .
                  BIND( IF( BOUND(?ej1st), ?ej1st, "__NULL__") AS ?_ej1st) .
                  BIND( IF( BOUND(?ej1et), ?ej1et, "__NULL__") AS ?_ej1et) .
                  BIND( IF( BOUND(?ej1ulx), ?ej1ulx, "__NULL__") AS ?_ej1ulx) .
                  BIND( IF( BOUND(?ej1uly), ?ej1uly, "__NULL__") AS ?_ej1uly) .
                  BIND( IF( BOUND(?ej1lrx), ?ej1lrx, "__NULL__") AS ?_ej1lrx) .
                  BIND( IF( BOUND(?ej1lry), ?ej1lry, "__NULL__") AS ?_ej1lry) .
              
                  BIND( cfn:getSpan(str(?docid), str(?edgecj1_doceid), str(?_ej1sid), str(?_ej1kfid), str(?_ej1so), str(?_ej1eo), str(?_ej1ulx), str(?_ej1uly), str(?_ej1lrx), str(?_ej1lry), str(?_ej1st), str(?_ej1et) ) as ?ej1_span ) .
              
              
                  # Get edge's justification span # 2
                  OPTIONAL {
                         ?edge_justification2 a                           aida:TextJustification .
                         ?edge_justification2 aida:startOffset            ?ej2so .
                         ?edge_justification2 aida:endOffsetInclusive     ?ej2eo
                  }
                  OPTIONAL {
                         ?edge_justification2 a                           aida:ImageJustification .
                         ?edge_justification2 aida:boundingBox            ?ej2bb  .
                         ?ej2bb                aida:boundingBoxUpperLeftX  ?ej2ulx .
                         ?ej2bb                aida:boundingBoxUpperLeftY  ?ej2uly .
                         ?ej2bb                aida:boundingBoxLowerRightX ?ej2lrx .
                         ?ej2bb                aida:boundingBoxLowerRightY ?ej2lry
                  }
                  OPTIONAL {
                         ?edge_justification2 a                           aida:KeyFrameVideoJustification .
                         ?edge_justification2 aida:keyFrame               ?ej2kfid .
                         ?edge_justification2 aida:boundingBox            ?ej2bb  .
                         ?ej2bb                aida:boundingBoxUpperLeftX  ?ej2ulx .
                         ?ej2bb                aida:boundingBoxUpperLeftY  ?ej2uly .
                         ?ej2bb                aida:boundingBoxLowerRightX ?ej2lrx .
                         ?ej2bb                aida:boundingBoxLowerRightY ?ej2lry
                  }
                  OPTIONAL {
                         ?edge_justification2 a                           aida:ShotVideoJustification .
                         ?edge_justification2 aida:shot                   ?ej2sid
                  }
                  OPTIONAL {
                         ?edge_justification2 a                           aida:AudioJustification .
                         ?edge_justification2 aida:startTimestamp         ?ej2st .
                         ?edge_justification2 aida:endTimestamp           ?ej2et
                  }
              
                  BIND( IF( BOUND(?ej2sid), ?ej2sid, "__NULL__") AS ?_ej2sid) .
                  BIND( IF( BOUND(?ej2kfid), ?ej2kfid, "__NULL__") AS ?_ej2kfid) .
                  BIND( IF( BOUND(?ej2so), ?ej2so, "__NULL__") AS ?_ej2so) .
                  BIND( IF( BOUND(?ej2eo), ?ej2eo, "__NULL__") AS ?_ej2eo) .
                  BIND( IF( BOUND(?ej2st), ?ej2st, "__NULL__") AS ?_ej2st) .
                  BIND( IF( BOUND(?ej2et), ?ej2et, "__NULL__") AS ?_ej2et) .
                  BIND( IF( BOUND(?ej2ulx), ?ej2ulx, "__NULL__") AS ?_ej2ulx) .
                  BIND( IF( BOUND(?ej2uly), ?ej2uly, "__NULL__") AS ?_ej2uly) .
                  BIND( IF( BOUND(?ej2lrx), ?ej2lrx, "__NULL__") AS ?_ej2lrx) .
                  BIND( IF( BOUND(?ej2lry), ?ej2lry, "__NULL__") AS ?_ej2lry) .
              
                  BIND( cfn:getSpan(str(?docid), str(?edgecj2_doceid), str(?_ej2sid), str(?_ej2kfid), str(?_ej2so), str(?_ej2eo), str(?_ej2ulx), str(?_ej2uly), str(?_ej2lrx), str(?_ej2lry), str(?_ej2st), str(?_ej2et) ) as ?ej2_span ) .
                  BIND(IF(?edge_num_cjs = 1, "", ?ej2_span) as ?ej2_span)
                  FILTER(?ej1_span > ?ej2_span)
                  BIND(IF(?edge_num_cjs = 1, ?ej1_span, CONCAT(CONCAT(?ej2_span,","),?ej1_span)) as ?ej_span)
              }
	]]>
END_SPARQL_QUERY
	$sparql;
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
	#$self->load();
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
		$self->add($query);
	}
}

sub add {
	my ($self, $query) = @_;
	$self->get("QUERIES")->add($query, $query->get("QUERYID"));
}

sub write_to_file {
	my ($self) = @_;
	my $query_type = $self->get("DTD_FILENAME");
	$query_type =~ s/^(.*?\/)+//g;
	$query_type =~ s/.dtd//;
	$query_type =~ s/query/queries/;
	open(my $program_output_xml, ">:utf8", $self->get("XML_FILENAME"))
		or $self->get("LOGGER")->record_problem('MISSING_FILE', $self->get("XML_FILENAME"), $!);
	print $program_output_xml "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
	print $program_output_xml "<$query_type>\n";
	print $program_output_xml $self->tostring(2);
	print $program_output_xml "<\/$query_type>\n";
	close($program_output_xml);
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
	$self->set("QUERYTYPE", $query_type);
	$self->set("REFERENCE_KBID", $self->get("XML_OBJECT")->get("CHILD", "reference_kbid")->get("ELEMENT"));
	$self->set("SPARQL", $self->get("XML_OBJECT")->get("CHILD", "sparql")->get("ELEMENT"));
}

#sub parse_object {
#	my ($self, $xml_object) = @_;
#	my $logger = $self->get("LOGGER");
#	my $retVal;
#	if($xml_object->get("CLASS") eq "XMLElement" && !ref $xml_object->get("ELEMENT")) {
#		# base-case of recursive function
#		my $key = uc($xml_object->get("NAME"));
#		my $value = $xml_object->get("ELEMENT");
#		if($xml_object->get("ATTRIBUTES") ne "nil") {
#			$retVal = SuperObject->new($logger);
#			$retVal->set($key, $value);
#			foreach my $attribute_key($xml_object->get("ATTRIBUTES")->get("ALL_KEYS")) {
#				my $attribute_value = $xml_object->get("ATTRIBUTES")->get("BY_KEY", $attribute_key);
#				$retVal->set($attribute_key, $attribute_value);
#			}
#		}
#		else {
#			$retVal = $value;
#		}
#	}
#	else {
#		if($xml_object->get("CLASS") eq "XMLElement") {
#			my $key = uc($xml_object->get("NAME"));
#			my $value = $self->parse_object($xml_object->get("ELEMENT"));
#			$retVal = SuperObject->new($logger);
#			$retVal->set($key, $value);
#			if($self->get("ATTRIBUTES") ne "nil") {
#				foreach my $attribute_key($self->get("ATTRIBUTES")->get("ALL_KEYS")) {
#					my $attribute_value = $self->get("ATTRIBUTES")->get("BY_KEY", $attribute_key);
#					$retVal->set($attribute_key, $attribute_value);
#				}
#			}
#		}
#		elsif($xml_object->get("CLASS") eq "XMLContainer") {
#			$retVal = SuperObject->new($logger);
#			foreach my $xml_element($xml_object->toarray()){
#				my $key = uc($xml_element->get("NAME"));
#				my $value = $self->parse_object($xml_element);
#				if($key =~ /.*?_DESCRIPTOR/) {
#					my $doceid = $value->get($key)->get("DOCEID");
#					my ($keyframeid, $start, $end);
#					if($key eq "TEXT_DESCRIPTOR") {
#						$start = $value->get($key)->get("START");
#						$end = $value->get($key)->get("END");
#					}
#					elsif($key eq "IMAGE_DESCRIPTOR") {
#						$start = $value->get($key)->get("TOPLEFT");
#						$end = $value->get($key)->get("BOTTOMRIGHT");
#					}
#					elsif($key eq "VIDEO_DESCRIPTOR") {
#						$keyframeid = $value->get($key)->get("KEYFRAMEID");
#						$start = $value->get($key)->get("TOPLEFT");
#						$end = $value->get($key)->get("BOTTOMRIGHT");
#					}
#					if($key eq "AUDIO_DESCRIPTOR") {
#						$start = $value->get($key)->get("START");
#						$end = $value->get($key)->get("END");
#					}
#					else{
#						# TODO: throw exception
#					}
#					$value = NonStringDescriptor->new($logger, $key, $doceid, $keyframeid, $start, $end);
#					$key = "DESCRIPTOR";
#				}
#				$retVal->set($key, $value);
#			}
#		}
#	}
#	$retVal;
#}

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
	$self->set("QUERYTYPE", $query_type);
	$self->set("PREDICATE", $self->get("XML_OBJECT")->get("CHILD", "predicate")->get("ELEMENT"));
	$self->set("SPARQL", $self->get("XML_OBJECT")->get("CHILD", "sparql")->get("ELEMENT"));
}

#
#sub parse_object {
#	my ($self, $xml_object) = @_;
#	my $logger = $self->get("LOGGER");
#	my $retVal;
#	if($xml_object->get("CLASS") eq "XMLElement" && !ref $xml_object->get("ELEMENT")) {
#		# base-case of recursive function
#		my $key = uc($xml_object->get("NAME"));
#		my $value = $xml_object->get("ELEMENT");
#		if($xml_object->get("ATTRIBUTES") ne "nil") {
#			$retVal = SuperObject->new($logger);
#			$retVal->set($key, $value);
#			foreach my $attribute_key($xml_object->get("ATTRIBUTES")->get("ALL_KEYS")) {
#				my $attribute_value = $xml_object->get("ATTRIBUTES")->get("BY_KEY", $attribute_key);
#				$retVal->set($attribute_key, $attribute_value);
#			}
#		}
#		else {
#			$retVal = $value;
#		}
#	}
#	else {
#		if($xml_object->get("CLASS") eq "XMLElement") {
#			my $key = uc($xml_object->get("NAME"));
#			my $value = $self->parse_object($xml_object->get("ELEMENT"));
#			$retVal = SuperObject->new($logger);
#			$retVal->set($key, $value);
#			if($xml_object->get("ATTRIBUTES") ne "nil") {
#				foreach my $attribute_key($xml_object->get("ATTRIBUTES")->get("ALL_KEYS")) {
#					my $attribute_value = $xml_object->get("ATTRIBUTES")->get("BY_KEY", $attribute_key);
#					$retVal->set($attribute_key, $attribute_value);
#				}
#			}
#		}
#		elsif($xml_object->get("CLASS") eq "XMLContainer") {
#			$retVal = SuperObject->new($logger);
#			foreach my $xml_element($xml_object->toarray()){
#				my $key = uc($xml_element->get("NAME"));
#				my $value = $self->parse_object($xml_element);
#				if($key =~ /.*?_DESCRIPTOR/ && $key ne "TYPED_DESCRIPTOR" && $key ne "STRING_DESCRIPTOR") {
#					my $doceid = $value->get($key)->get("DOCEID");
#					my ($keyframeid, $start, $end);
#					if($key eq "TEXT_DESCRIPTOR") {
#						$start = $value->get($key)->get("START");
#						$end = $value->get($key)->get("END");
#					}
#					elsif($key eq "IMAGE_DESCRIPTOR") {
#						$start = $value->get($key)->get("TOPLEFT");
#						$end = $value->get($key)->get("BOTTOMRIGHT");
#					}
#					elsif($key eq "VIDEO_DESCRIPTOR") {
#						$keyframeid = $value->get($key)->get("KEYFRAMEID");
#						$start = $value->get($key)->get("TOPLEFT");
#						$end = $value->get($key)->get("BOTTOMRIGHT");
#					}
#					if($key eq "AUDIO_DESCRIPTOR") {
#						$start = $value->get($key)->get("START");
#						$end = $value->get($key)->get("END");
#					}
#					else{
#						# TODO: throw exception
#					}
#					$value = NonStringDescriptor->new($logger, $key, $doceid, $keyframeid, $start, $end);
#					$key = "DESCRIPTOR";
#				}
#				elsif($key eq "STRING_DESCRIPTOR") {
#					$value = StringDescriptor->new($logger, $value->get($key));
#					$key = "DESCRIPTOR";
#				}
#				$value = $value->get($key) if($key eq "TYPED_DESCRIPTOR");
#				$retVal->set($key, $value);
#			}
#		}
#	}
#	$retVal;
#}
#
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

sub get_DOCIDS {
	my ($self, $docid_mappings, $scope) = @_;
	my $where = $self->get("WHERE");
	my @docids;
	my $doceid = $self->get("DOCEID");
	if($docid_mappings->get("DOCUMENTELEMENTS")->exists($doceid)) {
		my $docelement = $docid_mappings->get("DOCUMENTELEMENTS")->get("BY_KEY", $doceid);
		@docids = map {$_->get("DOCUMENTID")} $docelement->get("DOCUMENTS")->toarray();
	}
	else {
		$self->get("LOGGER")->record_problem("UNKNOWN_DOCUMENT_ELEMENT", $doceid, $where)
			if($scope ne "anywhere");
	}
	@docids;
}

sub get_MODALITY {
	my ($self) = @_;
	($self->get("TYPE") =~ /^(.*?)_/)[0];
}

sub tostring {
	my ($self) = @_;
	my ($filename, $keyframeid, $start, $end)
				= map {$self->get($_)} qw(DOCEID KEYFRAMEID START END);
	if($self->get("MODALITY") eq "TEXT" or $self->get("MODALITY") eq "AUDIO") {
		$start = "$start,0";
		$end = "$end,0";
	}
	$start = "($start)";
	$end = "($end)";
	$filename = $keyframeid if($self->get("MODALITY") eq "VIDEO");
	"$filename:$start-$end";
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

sub get_MODALITY {
	my ($self) = @_;
	($self->get("TYPE") =~ /^(.*?)_/)[0];
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
  my ($class, $logger, $filename, $coredocs) = @_;
  my $self = {
		CLASS => "DocumentIDsMappings",
		FILENAME => $filename,
		DOCUMENTS => Documents->new($logger),
    DOCUMENTELEMENTS => DocumentElements->new($logger),
    COREDOCS => $coredocs,
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
			my $is_core = 0;
			$is_core = 1 if $self->get("COREDOCS")->exists($document_id);
			my $document = $self->get("DOCUMENTS")->get("BY_KEY", $document_id);
			$document->set("DOCUMENTID", $document_id);
			$document->set("IS_CORE", $is_core);
			my $documentelement = $self->get("DOCUMENTELEMENTS")->get("BY_KEY", $document_eid);
			$documentelement->get("DOCUMENTS")->add($document, $document_id);
			$documentelement->set("DOCUMENTELEMENTID", $document_eid);
			$documentelement->set("TYPE", $detype);
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

sub get_IS_CORE {
	my ($self) = @_;
	my $is_core = 0;
	foreach my $document($self->get("DOCUMENTS")->toarray()) {
		$is_core = $is_core || $document->get("IS_CORE");
	}
	$self->set("IS_CORE", $is_core);
	$is_core;
}

#####################################################################################
# CoreDocs
#####################################################################################

package CoreDocs;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $filename) = @_;
  my $self = {
  	CLASS => 'CoreDocs',
  	FILENAME => $filename,
  	LOGGER => $logger,
  };
  bless($self, $class);
  $self->load();
  $self;
}

sub load {
	my ($self) = @_;
	my $filename = $self->get("FILENAME");
	my $filehandler = FileHandler->new($self->get("LOGGER"), $filename);
	my $entries = $filehandler->get("ENTRIES");
	foreach my $entry($entries->toarray()) {
		my $docid = $entry->get("root_id");
		$self->add("KEY", $docid);
	}
	$filehandler->cleanup();
}

#####################################################################################
# QREL
#####################################################################################

package QREL;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $filename, $query_type) = @_;
  my $self = {
  	CLASS => 'QREL',
  	FILENAME => $filename,
  	QUERY_TYPE => $query_type,
  	LOGGER => $logger,
  };
  bless($self, $class);
  $self->load();
  $self;
}

sub load {
	my ($self) = @_;
	my $filename = $self->get("FILENAME");
	my $filehandler = FileHandler->new($self->get("LOGGER"), $filename);
	my $entries = $filehandler->get("ENTRIES");
	foreach my $entry($entries->toarray()) {
		my ($nodeid, $docid, $mention_span, $assessment, $fqec, $where)
			= map {$entry->get($_)} qw(NODEID DOCID MENTION_SPAN ASSESSMENT FQEC WHERE);
		$self->{LOGGER}->record_problem("NO_FQEC_FOR_CORRECT_ENTRY", $where)
		  if $assessment eq "Correct" && !$fqec;
		my $key = "$nodeid:$mention_span";
		if($self->exists($key)) {
			my $existing_assessment = $self->get("BY_KEY", $key)->{"ASSESSMENT"};
			my $existing_linenum = $self->get("BY_KEY", $key)->{WHERE}{LINENUM};
			if($existing_assessment ne $assessment) {
				my $filename = $where->{FILENAME};
				$self->{LOGGER}->record_problem("MULTIPLE_INCOMPATIBLE_ZH_ASSESSMENTS",
													$nodeid,
													$mention_span,
													{FILENAME => $filename, LINENUM => "$existing_linenum, $where->{LINENUM}"});  
			}
		}
		$self->add({ASSESSMENT=>$assessment, DOCID => $docid, FQEC=> $fqec, WHERE=>$where}, $key)
			unless $self->exists($key);
	}
	$filehandler->cleanup();	
}

#####################################################################################
# ScoresManager
#####################################################################################

package ScoresManager;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $runid, $docid_mappings, $ldc_queries, $responses, $qrel, $query_type, @queries_to_score) = @_;
  my $self = {
  	CLASS => 'ScoresManager',
  	DOCID_MAPPINGS => $docid_mappings,
  	LDC_QUERIES => $ldc_queries,
  	RESPONSES => $responses,
  	QREL => $qrel,
  	QUERY_TYPE => $query_type,
  	QUERIES_TO_SCORE => [@queries_to_score],
		RUNID => $runid,
  	LOGGER => $logger,
  };
  bless($self, $class);
  $self->score_responses();
  $self;
}

sub score_responses {
	my ($self) = @_;
	my ($docid_mappings, $responses, $qrel, $query_type, $queries_to_score, $ldc_queries, $runid, $logger)
		= map {$self->get($_)} qw(DOCID_MAPPINGS RESPONSES QREL QUERY_TYPE QUERIES_TO_SCORE LDC_QUERIES RUNID LOGGER);
	my $scores;
	$scores = ClassScores->new($logger, $runid, $docid_mappings, $responses, $qrel, $ldc_queries, $queries_to_score) if($query_type eq "class_query");
	$scores = ZeroHopScores->new($logger, $runid, $docid_mappings, $responses, $qrel, $ldc_queries, $queries_to_score) if($query_type eq "zerohop_query");
	$scores = GraphScores->new($logger, $runid, $docid_mappings, $responses, $qrel, $ldc_queries, $queries_to_score) if($query_type eq "graph_query");
	$self->set("SCORES", $scores);
}

sub print_lines {
	my ($self, $program_output) = @_;
	$self->get("SCORES")->print_lines($program_output);
}

#####################################################################################
# ZeroHopScores
#####################################################################################

package ZeroHopScores;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $runid, $docid_mappings, $responses, $qrel, $ldc_queries, $queries_to_score) = @_;
  my $self = {
  	CLASS => 'ZeroHopScores',
  	DOCID_MAPPINGS => $docid_mappings,
  	LDC_QUERIES => $ldc_queries,
  	RESPONSES => $responses,
  	QREL => $qrel,
  	QUERIES_TO_SCORE => $queries_to_score,
		RUNID => $runid,
  	LOGGER => $logger,
  };
  bless($self, $class);
  $self->score_responses();
  $self;
}

sub score_responses {
	my ($self) = @_;
	my ($runid, $docid_mappings, $responses, $qrel, $queries_to_score, $ldc_queries, $logger)
		= map {$self->get($_)} qw(RUNID DOCID_MAPPINGS RESPONSES QREL QUERIES_TO_SCORE LDC_QUERIES LOGGER);
	my $scores = ScoresPrinter->new($logger);
	my %categorized_submissions;
	my %category_store;
	foreach my $key($qrel->get("ALL_KEYS")) {
		my ($node_id, $doceid, $start_and_end) = split(":", $key);
		if($doceid =~ /^(.*?)\_(\d+)$/){
			$doceid = $1;
		}
		my $mention_span = "$doceid:$start_and_end";
		my $assessment = $qrel->get("BY_KEY", $key)->{ASSESSMENT};
		my $fqec = $qrel->get("BY_KEY", $key)->{FQEC};
		my $docid = $qrel->get("BY_KEY", $key)->{DOCID};
		my $is_core = $docid_mappings->get("DOCUMENTELEMENTS")->get("BY_KEY", $doceid)->get("IS_CORE")
			if($docid_mappings->get("DOCUMENTELEMENTS")->exists($doceid));
		if ($assessment eq "Correct" && $is_core) {
			$category_store{GROUND_TRUTH}{$node_id}{$docid}{$fqec} = 1;			
			$category_store{GROUND_TRUTH}{$node_id}{"all"}{$fqec} = 1;
			$logger->record_debug_information("GROUND_TRUTH", 
								"NODEID=$node_id MENTION=$mention_span FQEC=$fqec CORRECT\n", 
								$qrel->get("BY_KEY", $key)->{WHERE});
		}
		elsif($assessment eq "Wrong" && $is_core) {
			$logger->record_debug_information("GROUND_TRUTH", 
								"NODEID=$node_id MENTION=$mention_span FQEC=$fqec INCORRECT\n", 
								$qrel->get("BY_KEY", $key)->{WHERE});
		}
	}
	foreach my $response($responses->get("RESPONSES")->toarray()) {
		my $query_id = $response->get("QUERYID");
		next unless grep {$query_id eq $_} @$queries_to_score;
		my $node_id = $ldc_queries->get("QUERY", $query_id)->get("ENTRYPOINT")->get("NODE");
		$node_id =~ s/^\?//;
		foreach my $justification($response->get("JUSTIFICATIONS")->toarray()) {
			my $doceid = $justification->get("DOCEID");
			my $is_core = $docid_mappings->get("DOCUMENTELEMENTS")->get("BY_KEY", $doceid)->get("IS_CORE")
				if($docid_mappings->get("DOCUMENTELEMENTS")->exists($doceid));
			my $mention_span = $justification->tostring();
			my $key = "$node_id:$mention_span";
			push(@{$categorized_submissions{$query_id}{"SUBMITTED"}}, $mention_span);
			my $fqec = "UNASSESSED";
			my %pre_policy = (SUBMITTED=>1);
			my %post_policy;
			if($qrel->exists($key) && $is_core) {
				my $assessment = $qrel->get("BY_KEY", $key)->{ASSESSMENT};
				$fqec = $qrel->get("BY_KEY", $key)->{FQEC};
				if($assessment eq "Correct") {
					push(@{$categorized_submissions{$query_id}{"CORRECT"}}, $mention_span);
					$pre_policy{CORRECT} = 1;
					if(exists $category_store{CORRECT_FOUND}{$query_id}{$fqec}) {
						push(@{$categorized_submissions{$query_id}{"REDUNDANT"}}, $mention_span);
						push(@{$categorized_submissions{$query_id}{"IGNORED"}}, $mention_span);
						$pre_policy{REDUNDANT} = 1;
						$post_policy{IGNORED} = 1;
					}
					else {
						$category_store{CORRECT_FOUND}{$query_id}{$fqec} = 1;
						push(@{$categorized_submissions{$query_id}{"RIGHT"}}, $mention_span);
						$post_policy{RIGHT} = 1;
					}
				}
				elsif($assessment eq "Wrong") {
					push(@{$categorized_submissions{$query_id}{"INCORRECT"}}, $mention_span);
					push(@{$categorized_submissions{$query_id}{"WRONG"}}, $mention_span);
					$pre_policy{INCORRECT} = 1;
					$post_policy{WRONG} = 1;
				}
			}
			else {
				push(@{$categorized_submissions{$query_id}{"NOT_IN_POOL"}}, $mention_span);
				push(@{$categorized_submissions{$query_id}{"IGNORED"}}, $mention_span);
				$pre_policy{NOT_IN_POOL} = 1;
				$post_policy{IGNORED} = 1;
			}
			my $pre_policy = join(",", sort keys %pre_policy);
			my $post_policy = join(",", sort keys %post_policy);
			my $line = "NODEID=$node_id " .
			           "QUERYID=$query_id " .
			           "MENTION=$mention_span " .
			           "PRE_POLICY_ASSESSMENT=$pre_policy " .
			           "POST_POLICY_ASSESSMENT=$post_policy " .
			           "FQEC=$fqec\n";
			$logger->record_debug_information("RESPONSE_ASSESSMENT", $line, $justification->get("WHERE"));
		}
	}
	foreach my $query_id(@$queries_to_score) {
		my $node_id = $ldc_queries->get("QUERY", $query_id)->get("ENTRYPOINT")->get("NODE");
		my $modality = $ldc_queries->get("QUERY", $query_id)->get("ENTRYPOINT")->get("DESCRIPTOR")->get("MODALITY");
		$node_id =~ s/^\?//;
		my $num_submitted = @{$categorized_submissions{$query_id}{"SUBMITTED"} || []};
		my $num_correct = @{$categorized_submissions{$query_id}{"CORRECT"} || []};
		my $num_incorrect = @{$categorized_submissions{$query_id}{"INCORRECT"} || []};
		my $num_right = @{$categorized_submissions{$query_id}{"RIGHT"} || []};
		my $num_wrong = @{$categorized_submissions{$query_id}{"WRONG"} || []};
		my $num_redundant = @{$categorized_submissions{$query_id}{"REDUNDANT"} || []};
		my $num_ignored = @{$categorized_submissions{$query_id}{"IGNORED"} || []};
		my $num_not_in_pool = @{$categorized_submissions{$query_id}{"NOT_IN_POOL"} || []};
		my $num_ground_truth = keys %{$category_store{GROUND_TRUTH}{$node_id}};
		my $score = Score->new($logger, $runid, $query_id, $node_id, $modality, $num_submitted, $num_correct, $num_incorrect, $num_right, $num_wrong, $num_redundant, $num_not_in_pool, $num_ignored, $num_ground_truth);
		$scores->add($score, $query_id);
	}
	$self->set("SCORES", $scores);
}

sub print_lines {
	my ($self, $program_output) = @_;
	$self->get("SCORES")->print_lines($program_output);
}

#####################################################################################
# ScoresPrinter
#####################################################################################

package ScoresPrinter;

use parent -norequire, 'Container', 'Super';

my @fields_to_print = (
  {NAME => 'EC',               HEADER => 'QID/EC',   FORMAT => '%s',     JUSTIFY => 'L'},
  {NAME => 'NODEID',           HEADER => 'Node',     FORMAT => '%s',     JUSTIFY => 'L'},
  {NAME => 'MODALITY',         HEADER => 'Mode',     FORMAT => '%s',     JUSTIFY => 'L'},
  {NAME => 'RUNID',            HEADER => 'RunID',    FORMAT => '%s',     JUSTIFY => 'L'},
  {NAME => 'NUM_GROUND_TRUTH', HEADER => 'GT',       FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_SUBMITTED',    HEADER => 'Sub',      FORMAT => '%4d',    JUSTIFY => 'R'},
  {NAME => 'NUM_NOT_IN_POOL',  HEADER => 'NtAssd',   FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_CORRECT',      HEADER => 'Correct',  FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_REDUNDANT',    HEADER => 'Dup',      FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_INCORRECT',    HEADER => 'Incrct',   FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_COUNTED',      HEADER => 'Cntd',     FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_RIGHT',        HEADER => 'Right',    FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_WRONG',        HEADER => 'Wrong',    FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_IGNORED',      HEADER => 'Ignrd',    FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'PRECISION',        HEADER => 'Prec',     FORMAT => '%6.4f',  JUSTIFY => 'L'},
  {NAME => 'RECALL',           HEADER => 'Recall',   FORMAT => '%6.4f',  JUSTIFY => 'L'},
  {NAME => 'F1',               HEADER => 'F1',       FORMAT => '%6.4f',  JUSTIFY => 'L'},
);

sub new {
  my ($class, $logger, $program_output) = @_;
  my $self = $class->SUPER::new($logger, 'Score');
  $self->{CLASS} = 'ScoresPrinter';
  $self->{PROGRAM_OUTPUT} = $program_output;
  $self->{WIDTHS} = {map {$_->{NAME} => length($_->{HEADER})} @fields_to_print};
  $self->{LOGGER} = $logger;
  $self->{LINES} = [];
  @{$self->{FIELDS_TO_PRINT}} = @fields_to_print;
  bless($self, $class);
  $self;
}

sub get_MICRO_AVERAGE {
	my ($self) = @_;
	my $logger = $self->get("LOGGER");
	my ($runid, $total_num_submitted, $total_num_correct, $total_num_incorrect, $total_num_right, $total_num_wrong, $total_num_redundant, $total_num_not_in_pool, $total_num_ignored, $total_num_ground_truth);
	foreach my $score($self->toarray()) {
		my ($num_submitted, $num_correct, $num_incorrect, $num_right, $num_wrong, $num_redundant, $num_not_in_pool, $num_ignored, $num_ground_truth)
			= map {$score->get($_)} qw(NUM_SUBMITTED NUM_CORRECT NUM_INCORRECT NUM_RIGHT NUM_WRONG NUM_REDUNDANT NUM_NOT_IN_POOL NUM_IGNORED NUM_GROUND_TRUTH);
		$runid = $score->get("RUNID") unless $runid;
		$total_num_submitted += $num_submitted;
		$total_num_correct += $num_correct;
		$total_num_incorrect += $num_incorrect;
		$total_num_right += $num_right;
		$total_num_wrong += $num_wrong;
		$total_num_redundant += $num_redundant;
		$total_num_not_in_pool += $num_not_in_pool;
		$total_num_ignored += $num_ignored;
		$total_num_ground_truth += $num_ground_truth;
	}
	Score->new($logger, $runid, "ALL-Micro", "", "", $total_num_submitted, $total_num_correct, $total_num_incorrect, $total_num_right, $total_num_wrong, $total_num_redundant, $total_num_not_in_pool, $total_num_ignored, $total_num_ground_truth);
}

sub print_line {
  my ($self, $line) = @_;
  my $program_output = $self->get("PROGRAM_OUTPUT");
  my $separator = "";
  foreach my $field (@{$self->{FIELDS_TO_PRINT}}) {
    my $value = (defined $line ? $line->{$field->{NAME}} : $field->{HEADER});
    print $program_output $separator;
    my $numspaces = defined $self->{SEPARATOR} ? 0 : $self->{WIDTHS}{$field->{NAME}} - length($value);
    print $program_output ' ' x $numspaces if $field->{JUSTIFY} eq 'R' && !defined $self->{SEPARATOR};
    print $program_output $value;
    print $program_output ' ' x $numspaces if $field->{JUSTIFY} eq 'L' && !defined $self->{SEPARATOR};
    $separator = defined $self->{SEPARATOR} ? $self->{SEPARATOR} : ' ';
  }
  print $program_output "\n";
}
  
sub print_headers {
  my ($self) = @_;
  $self->print_line();
}

sub prepare_lines {
	my ($self) = @_;
	my @scores = $self->toarray();
	push(@scores, $self->get("MICRO_AVERAGE"));
	foreach my $score (@scores) {
		my %elements_to_print;
		foreach my $field (@{$self->{FIELDS_TO_PRINT}}) {
			my $value = $score->get($field->{NAME});
			my $text = sprintf($field->{FORMAT}, $value);
			$elements_to_print{$field->{NAME}} = $text;
			$self->{WIDTHS}{$field->{NAME}} = length($text) if length($text) > $self->{WIDTHS}{$field->{NAME}};
		}
		push(@{$self->{LINES}}, \%elements_to_print);
	}
}

sub print_lines {
  my ($self, $program_output) = @_;
  $self->set("PROGRAM_OUTPUT", $program_output);
  $self->prepare_lines();
  $self->print_headers();
  foreach my $line (@{$self->{LINES}}) {
    $self->print_line($line);
  }
}

#####################################################################################
# Score
#####################################################################################

package Score;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $runid, $query_id, $node_id, $modality, $num_submitted, $num_correct, $num_incorrect, $num_right, $num_wrong, $num_redundant, $num_not_in_pool, $num_ignored, $num_ground_truth) = @_;
  my $self = {
		CLASS => 'Scores',
		EC => $query_id,
		MODALITY => $modality,
		NODEID => $node_id,
		NUM_CORRECT => $num_correct,
		NUM_GROUND_TRUTH => $num_ground_truth,
		NUM_IGNORED => $num_ignored,
		NUM_INCORRECT => $num_incorrect,
		NUM_NOT_IN_POOL => $num_not_in_pool,
		NUM_REDUNDANT => $num_redundant,
		NUM_RIGHT => $num_right,
		NUM_SUBMITTED => $num_submitted,
		NUM_WRONG => $num_wrong,
		RUNID => $runid,
		LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub get_NUM_COUNTED {
	my ($self) = @_;
	$self->get("NUM_RIGHT") + $self->get("NUM_WRONG");
}

sub get_PRECISION {
	my ($self) = @_;
	$self->get("NUM_COUNTED") ? $self->get("NUM_RIGHT")/($self->get("NUM_COUNTED")) : 0;
}

sub get_RECALL {
	my ($self) = @_;
	$self->get("NUM_GROUND_TRUTH") ? $self->get("NUM_RIGHT")/($self->get("NUM_GROUND_TRUTH")) : 0;
}

sub get_F1 {
	my ($self) = @_;
	my $precision = $self->get("PRECISION");
	my $recall = $self->get("RECALL");
	($precision + $recall) ? 2*$precision*$recall/($precision + $recall) : 0;
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