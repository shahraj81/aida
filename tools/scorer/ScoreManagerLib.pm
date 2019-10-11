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

### BEGIN INCLUDE Super
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
  die "Abstract method 'get_BY_INDEX' not defined in derived class '", $self->get("__CLASS__") ,"'\n";
}

sub get_BY_KEY {
  my ($self) = @_;
  die "Abstract method 'get_BY_KEY' not defined in derived class '", $self->get("__CLASS__") ,"'\n";
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
### END INCLUDE Super

### BEGIN INCLUDE SuperObject
#####################################################################################
# SuperObject
#####################################################################################

package SuperObject;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = {
    __CLASS__ => 'SuperObject',
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}
### END INCLUDE SuperObject

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
  AP_SUBMISSION_LINE                      DEBUG_INFO     AP_SUBMISSION_LINE: %s
  CORRECT_EDGE                            DEBUG_INFO     CORRECT_EDGE: %s
  DUPLICATE_IN_POOLED_RESPONSE            DEBUG_INFO     Response: %s already in pool therefore skipping
  DUPLICATE_QUERY                         DEBUG_INFO     Query %s (file: %s) is a duplicate of %s (file: %s) therefore skipping it
  DISCONNECTED_VALID_GRAPH                WARNING        Considering only valid edges, the graph in submission is not fully connected
  GROUND_TRUTH                            DEBUG_INFO     GROUND_TRUTH_INFO: %s     
  EMPTY_FILE_TO_LOAD                      WARNING        Trying to load empty file %s
  EXTRA_EDGE_JUSTIFICATIONS               WARNING        Extra edge justifications (expected <= %s; provided %s)
  FRAME_QUERY                             DEBUG_INFO     FRAME_QUERY: %s
  ID_WITH_EXTENSION                       ERROR          File extension provided as part of %s %s
  ILLEGAL_CONFIDENCE_VALUE                ERROR          Illegal confidence value: %s
  ILLEGAL_IMPORTANCE_VALUE                ERROR          Illegal importance value: %s
  IMPROPER_CONFIDENCE_VALUE               WARNING        Confidence value in scientific format: %s
  IMPROPER_IMPORTANCE_VALUE               WARNING        Importance value in scientific format: %s
  INCORRECT_PROVENANCE_FORMAT             ERROR          Incorrect format of provenance %s
  INVALID_CONFIDENCE                      WARNING        Invalid confidence %s in response
  INVALID_END                             WARNING        Invalid end %s in response justification of type %s
  INVALID_JUSTIFICATION_TYPE              ERROR          Invalid justification type %s
  INVALID_KEYFRAMEID                      WARNING        Invalid keyframeid %s
  INVALID_START                           WARNING        Invalid start %s in %s
  MISMATCHING_COLUMNS                     FATAL_ERROR    Mismatching columns (header:%s, entry:%s) %s %s
  MISSING_DECIMAL_POINT                   WARNING        Decimal point missing in confidence value: %s
  MISSING_FILE                            FATAL_ERROR    Could not open %s: %s
  MISSING_KEYFRAMEID                      ERROR          Missing keyframeid in video provenance %s (expecting %s, provided %s)
  MULTIPLE_DOCUMENTS                      ERROR          Multiple documents used in response: %s, %s (expected exactly one)
  MULTIPLE_ENTRIES_IN_A_CLUSTER           ERROR          Multiple response entries in the cluster %s (expected no more than one)
  MULTIPLE_INCOMPATIBLE_ZH_ASSESSMENTS    ERROR          Multiple incompatible assessments provided (node: %s, mention_span: %s)
  MULTIPLE_INFORMATIVE_JUSTIFICATIONS_PER_DOCUMENT WARNING Multiple informative justification for run_and_query %s, cluster %s and document %s
  MULTIPLE_GRAPH_ASSESSMENTS              ERROR          Multiple assessments for entry key %s in files (%s:line # %s, %s: line # %s)
  MULTIPLE_JUSTIFYING_DOCS                ERROR          Multiple justifying documents: %s (expected only one)
  MULTIPLE_POTENTIAL_ROOTS                FATAL_ERROR    Multiple potential roots "%s" in query DTD file: %s
  MULTIPLE_TASK_AND_TYPE_IN_QUERIES       FATAL_ERROR    Queries with mixed task and type found in query set, for e.g. %s and %s
  NO_FQEC_FOR_CORRECT_ENTRY               ERROR          No FQEC found for a correct entry
  NO_QUERY_FOR_ASSESSNENT_ITEM            DEBUG_INFO     No query found for assessment entry: %s
  NON_NUMERIC_VAL                         ERROR          Value %s is not numeric
  NONNUMERIC_START                        WARNING        Start %s is not numeric
  PARENT_CHILD_RELATION_FAILURE           ERROR          %s is not a child of %s
  PARAMETER_KEY_EXISTS                    WARNING        Key %s used multiple times
  RESPONSE_ASSESSMENT                     DEBUG_INFO     ASSESSMENT_INFO: %s
  RUNS_HAVE_MULTIPLE_TASKS                ERROR          Response files in the pathfile include task1 and task2 responses; expected responses files corresponding to exactly one task
  SALIENT_READ                            DEBUG_INFO     SALIENT_READ: %s
  SALIENT_FOR_QUERY                       DEBUG_INFO     SALIENT_FOR_QUERY: %s
  SKIPPING_CLUSTER_NOT_SELECTED           DEBUG_INFO     Skipping because cluster is not selected: %s
  SKIPPING_INPUT_FILE                     DEBUG_INFO     Skipping over file %s
  SKIPPING_RESPONSE_CLUSTER_INCLUDED      DEBUG_INFO     Skipping because response from the cluster is already selected: %s
  SPAN_OFF_BOUNDARY                       ERROR          Provenance %s is outside the boundary %s of document element %s          
  START_LARGER_THAN_END                   ERROR          Start (%s) is larger than (%s) in provenance %s
  UNDEFINED_FUNCTION                      FATAL_ERROR    Function %s not defined in package %s
  UNEXPECTED_CLUSTER_MEMBER_TYPE          ERROR          Unexpected cluster member type (expected %s, provided %s)
  UNEXPECTED_COLUMN_HEADER                ERROR          Unexpected column # %s (expected %s, provided %s)
  UNEXPECTED_COLUMN_NUM                   ERROR          Unexpected number of columns (expected %s, provided %s)
  UNEXPECTED_DOCUMENT_ID                  ERROR          Unexpected document %s (expected %s)
  UNEXPECTED_EDGETYPE                     ERROR          Unexpected edge %s in response (expected %s)
  UNEXPECTED_ENTTYPE                      ERROR          Unexpected enttype %s in response (expected %s)
  UNEXPECTED_EVENTTYPE                    ERROR          Unexpected event type %s in response (expected %s)
  UNEXPECTED_LINK_TARGET                  ERROR          Unexpected link target %s in response (expected %s)
  UNEXPECTED_NUM_SPANS                    ERROR          Unexpected number of spans in provenance %s (expected %s, provided %s)
  UNEXPECTED_OUTPUT_TYPE                  FATAL_ERROR    Unknown output type %s
  UNEXPECTED_PARAMETER_LINE               WARNING        Unexpected line in the parameters file
  UNEXPECTED_QUERY_TYPE                   FATAL_ERROR    Unexpected query type %s
  UNEXPECTED_ROLENAME                     ERROR          Unexpected role name %s in response (expected %s)
  UNKNOWN_DOCUMENT                        ERROR          Unknown Document %s in response
  UNKNOWN_DOCUMENT_ELEMENT                ERROR          Unknown DocumentElement %s in response
  UNKNOWN_EDGEID                          WARNING        Unknown edge %s in response to query %s
  UNKNOWN_KEYFRAMEID                      ERROR          Unknown keyframeid %s
  UNKNOWN_MODALITY                        ERROR          Unknown modality for document element %s
  UNKNOWN_QUERYID                         WARNING        Unknown query %s in response
  UNKNOWN_RESPONSE_FILE_TYPE              ERROR          Unknown response type of file %s
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
sub get_error_code {
  my ($self) = @_;
  255;
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
  exit $self->get_error_code();
}

### END INCLUDE Logger

### BEGIN INCLUDE Container
#####################################################################################
# Container
#####################################################################################

package Container;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $element_class) = @_;
  $element_class = "RAW" unless $element_class;
  my $self = {
    __CLASS__ => 'Container',
    __ELEMENT_CLASS__ => $element_class,
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
    $self->get("LOGGER")->record_problem("MISSING_RAW_KEY", $key, $self->get("__ELEMENT_CLASS__"), $where)
      if $self->get("__ELEMENT_CLASS__") eq "RAW";
    my $element = $self->get("__ELEMENT_CLASS__")->new($self->get("LOGGER"));
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
### END INCLUDE Container

### BEGIN INCLUDE FileHandler
#####################################################################################
# File Handler
#####################################################################################

package FileHandler;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $filename, $header) = @_;
  my $self = {
    __CLASS__ => 'FileHandler',
    FILENAME => $filename,
    HEADER => $header,
    ENTRIES => Container->new($logger),
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->get("LOGGER")->record_problem("EMPTY_FILE_TO_LOAD", $filename, {FILENAME => __FILE__, LINENUM => __LINE__})
    if -z $filename;
  $self->load($filename) unless -z $filename;
  $self;
}

sub load {
  my ($self, $filename) = @_;

  my $linenum = 0;

  open(FILE, "<:utf8", $filename) or $self->get("LOGGER")->record_problem('MISSING_FILE', $filename, {FILENAME => __FILE__, LINENUM => __LINE__});
  my $line;
  unless($self->{HEADER}) {
    $line = <FILE>; 
    $line =~ s/\r\n?//g;
    chomp $line;
    $linenum++;
    $self->{HEADER} = Header->new($self->get("LOGGER"), $line);
  }

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
### END INCLUDE FileHandler

### BEGIN INCLUDE Header
#####################################################################################
# Header
#####################################################################################

package Header;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $line, $field_separator) = @_;
  $field_separator = "\t" unless $field_separator;
  my $self = {
    __CLASS__ => 'Header',
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
### END INCLUDE Header

### BEGIN INCLUDE Entry
#####################################################################################
# Entry
#####################################################################################

package Entry;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $linenum, $line, $header, $where, $field_separator) = @_;
  $field_separator = "\t" unless $field_separator;
  my $self = {
    __CLASS__ => 'Entry',
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
### END INCLUDE Entry

#####################################################################################
# Parameters
#####################################################################################

package Parameters;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $filename) = @_;
  my $self = {
    __CLASS__ => 'Parameters',
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
    __CLASS__ => 'DTD',
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
    __CLASS__ => 'Tree',
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
  $self->{__CLASS__} = 'Nodes';
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
    __CLASS__ => 'Node',
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
#  my ($self, $child) = @_;
#  $self->get("CHILDREN")->add($child, $child->get("NODEID"));
#}

#sub add_TYPE {
#  my ($self, $type) = @_;
#  $self->get("TYPES")->add("KEY", $type);
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
    __CLASS__ => "XMLFileHandler",
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
    __CLASS__ => 'XMLAttributes',
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
    __CLASS__ => 'XMLElement',
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
  $self->{__CLASS__} = 'XMLContainer';
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

use Scalar::Util qw(looks_like_number);

my $anything_pattern = qr/.+/;
my $provenance_triple_pattern = qr/[^:]+:\d+-\d+/;
my $provenance_triples_pattern = qr/(?:[^:]+:\d+-\d+,){0,3}[^:]+:\d+-\d+/;

my %validators = (
  # Check if the confidence is a numeric value and falls is inside (0,1]
  'CONFIDENCE' => {
    NAME => 'CONFIDENCE',
    VALIDATE => sub {
      my ($responses, $logger, $where, $queries, $schema, $column, $entry, $column_name) = @_;
      my $value = $entry->get($column_name);
      return 1 if($schema->{TASK} eq "task3" && $schema->{QUERY_TYPE} eq "GRAPH" && $value eq "NULL" && $column_name eq "EDGE_COMPOUND_JUSTIFICATION_CONFIDENCE");
      unless ($value =~ /^(?:1\.0*)$|^(?:0?\.[0-9]*[1-9][0-9]*)$/) {
        $logger->record_problem('ILLEGAL_CONFIDENCE_VALUE', $value, $where);
        return;
      }
      1;
    },
  },
  # Check if DocumentID belongs to the corpus
  'DOCUMENT_ID' => {
    NAME => 'DOCUMENT_ID',
    VALIDATE => sub {
      my ($responses, $logger, $where, $queries, $schema, $column, $entry, $column_name) = @_;
      my $entry_document_id = $entry->get($column_name);
      unless ($responses->get("DOCID_MAPPINGS")->get("DOCUMENTS")->exists($entry_document_id)) {
        $logger->record_problem("UNKNOWN_DOCUMENT", $entry_document_id, $where);
        return;
      }
      if($schema->{TASK} eq "task1") {
        my $kb_documentid = $entry->get("KB_DOCUMENT_ID");
        # Check if the document matches the document from which the KB was generated
        if($entry_document_id ne $kb_documentid) {
          $logger->record_problem("UNEXPECTED_DOCUMENT_ID", $entry_document_id, $kb_documentid, $where);
          return;
        }
      }
      1;
    },
  },
  # Check if importance value is valid
  'IMPORTANCE' => {
    NAME => 'IMPORTANCE',
    VALIDATE => sub {
      my ($responses, $logger, $where, $queries, $schema, $column, $entry, $column_name) = @_;
      my $value = $entry->get($column_name);
      unless (looks_like_number($value)) {
        $logger->record_problem('ILLEGAL_IMPORTANCE_VALUE', $value, $where);
        return;
      }
      1;
    },
  },

  # Check if for TA1 system all responses come from the same (parent) document
  'KB_DOCUMENT_ID' => {
    NAME => 'KB_DOCUMENT_ID',
    VALIDATE => sub {
      my ($responses, $logger, $where, $queries, $schema, $column, $entry, $column_name) = @_;
      my $kb_documentid = $entry->get($column_name);
      my $entry_documentid = $entry->get("DOCUMENT_ID");
      my $task = $schema->{TASK};
      if($task eq "task1") {
        unless ($kb_documentid eq $entry_documentid) {
          $logger->record_problem("UNEXPECTED_DOCUMENT_ID", $entry_documentid, $kb_documentid, $where);
          return;
        }
      }
      1;
    },
  },

  'MATCHING_EDGE_TYPE_IN_RESPONSE' => {
    NAME => 'MATCHING_EDGE_TYPE_IN_RESPONSE',
    VALIDATE => sub {
      my ($responses, $logger, $where, $queries, $schema, $column, $entry, $column_name) = @_;
      my $edgetype_in_query = $entry->get("QUERY")->get("PREDICATE");
      my $matching_edgetype_in_response = $entry->get("MATCHING_EDGE_TYPE_IN_RESPONSE");
      ($matching_edgetype_in_response) = $matching_edgetype_in_response =~ /\#(.*?)\>/;
      my ($event_or_relation_type_in_query, $rolename_in_query) = split("_",$edgetype_in_query);
      my ($matching_event_or_relation_type_in_response, $matching_rolename_in_response) = split("_",$matching_edgetype_in_response);
      unless ($rolename_in_query eq $matching_rolename_in_response) {
        $logger->record_problem("UNEXPECTED_ROLENAME", $matching_rolename_in_response, $rolename_in_query, $where);
        return;
      }
      unless ($matching_event_or_relation_type_in_response eq $event_or_relation_type_in_query || $matching_event_or_relation_type_in_response =~ /^$event_or_relation_type_in_query\..*?$/) {
        $logger->record_problem("UNEXPECTED_EVENTTYPE", $matching_event_or_relation_type_in_response, "$event_or_relation_type_in_query or $event_or_relation_type_in_query\.*", $where);
        return;
      }
      1;
    },
  },

  'MATCHING_ENTITY_TYPE_IN_RESPONSE' => {
    NAME => 'MATCHING_ENTITY_TYPE_IN_RESPONSE',
    VALIDATE => sub {
      my ($responses, $logger, $where, $queries, $schema, $column, $entry, $column_name) = @_;
      my $enttype_in_query = $entry->get("QUERY")->get("ENTTYPE");
      my $matching_enttype_in_response = $entry->get("MATCHING_ENTITY_TYPE_IN_RESPONSE");
      ($matching_enttype_in_response) = $matching_enttype_in_response =~ /\#(.*?)\>/;
      unless ($matching_enttype_in_response eq $enttype_in_query || $matching_enttype_in_response =~ /^$enttype_in_query\..*?$/) {
        $logger->record_problem("UNEXPECTED_ENTTYPE", $matching_enttype_in_response, "$enttype_in_query or $enttype_in_query\.*", $where);
        return;
      }
      1;
    },
  },

  'MATCHING_LINK_TARGET_IN_RESPONSE' => {
    NAME => 'MATCHING_LINK_TARGET_IN_RESPONSE',
    VALIDATE => sub {
      my ($responses, $logger, $where, $queries, $schema, $column, $entry, $column_name) = @_;
      my $linktargets_in_query = $entry->get("QUERY")->get("REFERENCE_KBID");
      $linktargets_in_query = $entry->get("QUERY")->get("OBJECT") if($schema->{QUERY_TYPE} eq "GRAPH");
      my @linktargets_in_query = split(/\|/, $linktargets_in_query);
      my $matching_linktarget_in_response = $entry->get("MATCHING_LINK_TARGET_IN_RESPONSE");
      unless (grep {$matching_linktarget_in_response eq $_} @linktargets_in_query) {
        $logger->record_problem("UNEXPECTED_LINK_TARGET", $matching_linktarget_in_response, $linktargets_in_query, $where);
        return;
      }
      1;
    },
  },

  'QUERY_EDGE_TYPE_IN_RESPONSE' => {
    NAME => 'QUERY_EDGE_TYPE_IN_RESPONSE',
    VALIDATE => sub {
      my ($responses, $logger, $where, $queries, $schema, $column, $entry, $column_name) = @_;
      my $edgetype_in_query = $entry->get("QUERY")->get("PREDICATE");
      my $edgetype_in_response = $entry->get("QUERY_EDGE_TYPE_IN_RESPONSE");
      ($edgetype_in_response) = $edgetype_in_response =~ /\#(.*?)\>/;
      unless ($edgetype_in_response eq $edgetype_in_query) {
        $logger->record_problem("UNEXPECTED_EDGETYPE", $edgetype_in_response, $edgetype_in_query, $where);
        return;
      }
      1;
    },
  },

  'QUERY_ENTITY_TYPE_IN_RESPONSE' => {
    NAME => 'QUERY_ENTITY_TYPE_IN_RESPONSE',
    VALIDATE => sub {
      my ($responses, $logger, $where, $queries, $schema, $column, $entry, $column_name) = @_;
      my $enttype_in_query = $entry->get("QUERY")->get("ENTTYPE");
      my $enttype_in_response = $entry->get("QUERY_ENTITY_TYPE_IN_RESPONSE");
      ($enttype_in_response) = $enttype_in_response =~ /\#(.*?)\>/;
      unless ($enttype_in_response eq $enttype_in_query) {
        $logger->record_problem("UNEXPECTED_ENTTYPE", $enttype_in_response, $enttype_in_query, $where);
        return;
      }
      1;
    },
  },

  'QUERY_LINK_TARGET_IN_RESPONSE' => {
    NAME => 'QUERY_LINK_TARGET_IN_RESPONSE',
    VALIDATE => sub {
      my ($responses, $logger, $where, $queries, $schema, $column, $entry, $column_name) = @_;
      my $linktargets_in_query = $entry->get("QUERY")->get("REFERENCE_KBID");
      $linktargets_in_query = $entry->get("QUERY")->get("OBJECT") if($schema->{QUERY_TYPE} eq "GRAPH");
      my $linktarget_in_response = $entry->get("QUERY_LINK_TARGET_IN_RESPONSE");
      unless ($linktarget_in_response eq $linktargets_in_query) {
        $logger->record_problem("UNEXPECTED_LINK_TARGET", $linktarget_in_response, $linktargets_in_query, $where);
        return;
      }
      1;
    },
  },

  'SUBJECT_TYPE' => {
    NAME => 'SUBJECT_TYPE',
    VALIDATE => sub {
      my ($responses, $logger, $where, $queries, $schema, $column, $entry, $column_name) = @_;
      if($schema->{TASK} eq "task3" && $schema->{QUERY_TYPE} eq "GRAPH") {
        my $subject_type = $entry->get($column_name);
        my $subject_cluster_id = $entry->get("SUBJECT_CLUSTER_ID");
        $responses->get("CLUSTER_TYPES")->add($subject_type, $subject_cluster_id)
          unless($responses->get("CLUSTER_TYPES")->exists($subject_cluster_id));
        my $cluster_type = $responses->get("CLUSTER_TYPES")->get("BY_KEY", $subject_cluster_id);
        $logger->record_problem("UNEXPECTED_CLUSTER_MEMBER_TYPE", $cluster_type, $subject_type, $where)
          if $subject_type ne $cluster_type;
      }
      1;
    },
  },

  # Check if DocumentElement and Document have parent-child relationship
  # Check if provenance falls within the boundaries
  'VALUE_PROVENANCE_TRIPLE' => {
    NAME => 'VALUE_PROVENANCE_TRIPLE',
    VALIDATE => sub {
      my ($responses, $logger, $where, $queries, $schema, $column, $entry, $column_name) = @_;
      my $optional = 0;
      $optional = 1 if $column->{OPTIONAL};
      my $provenance = $entry->get($column_name);
      return 1 if($schema->{TASK} eq "task3" && $schema->{QUERY_TYPE} eq "GRAPH" && $provenance eq "NULL");
      return 1 if $optional && !$provenance;
      unless(split(":", $provenance) == 3) {
        $logger->record_problem("INCORRECT_PROVENANCE_FORMAT", $provenance, $where);
        return;
      }
      unless($provenance =~ /^.*?:.*?:\(\d+,\d+\)-\(\d+,\d+\)$/) {
        $logger->record_problem("INCORRECT_PROVENANCE_FORMAT", $provenance, $where);
        return;
      }
      my ($document_id, $document_element_id, $span) = $provenance =~ /^(.*?):(.*?):(\((\d+?),(\d+?)\)-\((\d+?),(\d+?)\))$/;
      my $keyframe_id;
      if($document_element_id =~ /^(.*?)_/) {
        $keyframe_id =  $document_element_id;
        $document_element_id = $1;
      }
      if($document_element_id =~ /\.(gif|jpg|png)$/) {
        $logger->record_problem("ID_WITH_EXTENSION", "document element id", $document_element_id, $where);
        return;
      }
      unless($document_id eq $entry->get("DOCUMENT_ID")) {
        $logger->record_problem("MULTIPLE_DOCUMENTS", $document_id, $entry->get("DOCUMENT_ID"), $where);
        return;
      }
      my $document_elements = $responses->get("DOCID_MAPPINGS")->get("DOCUMENTELEMENTS");
      my $documents = $responses->get("DOCID_MAPPINGS")->get("DOCUMENTS");

      unless ($document_elements->exists($document_element_id)) {
        $logger->record_problem("UNKNOWN_DOCUMENT_ELEMENT", $document_element_id, $where);
        return;
      }
      my $document_element = $document_elements->get("BY_KEY", $document_element_id);
      unless ($document_element->get("MODALITY")) {
        $logger->record_problem("UNKNOWN_MODALITY", $document_element_id, $where);
        return;
      }
      my $modality = $document_element->get("MODALITY");
      if($modality eq "VIDEO") {
        unless($keyframe_id) {
          $logger->record_problem("MISSING_KEYFRAMEID", $provenance, "$document_element_id\_\\d+", $document_element_id, $where);
          return;
        }
        else {
          # keyframeid can't have extension
          if($keyframe_id =~ /\.(gif|jpg|png)$/) {
            $logger->record_problem("ID_WITH_EXTENSION", "keyframeid", $document_element_id, $where);
            return;
          }
          unless($responses->get("KEYFRAME_BOUNDARIES")->exists($keyframe_id)) {
            $logger->record_problem("UNKNOWN_KEYFRAMEID", $keyframe_id, $where);
            return;
          }
        }
      }
      my $document = $documents->get("BY_KEY", $document_id);
      unless($document->get("DOCUMENTELEMENTS")->exists($document_element_id)) {
        $logger->record_problem("PARENT_CHILD_RELATION_FAILURE", $document_element_id, $document_id, $where);
        return;
      }
      my ($sx, $sy, $ex, $ey) = $span =~ /\((\d+?),(\d+?)\)-\((\d+?),(\d+?)\)/;
      # check if the span mentioned in the provenance contains numeric values
      foreach my $value(($sx, $sy, $ex, $ey)) {
        $logger->record_problem("NON_NUMERIC_VAL", $value, $where)
          unless looks_like_number($value);
        $logger->record_problem("NEGATIVE_VAL", $value, $where)
          if looks_like_number($value) && $value < 0;
      }
      # check if start < end 
      foreach my $start_and_end ({START=>$sx, END=>$ex}, {START=>$sy, END=>$ey}) {
        $logger->record_problem("START_LARGER_THAN_END", $start_and_end->{START}, $start_and_end->{END}, $provenance, $where)
         if looks_like_number($start_and_end->{START}) 
            && looks_like_number($start_and_end->{END}) 
            && $start_and_end->{START} > $start_and_end->{END};
      }
      # check if the span mentioned in the provenance is within the document element boundary
      my $document_element_boundary;
      $document_element_boundary = $responses->get("TEXT_BOUNDARIES")->get("BY_KEY", $document_element_id) if($modality eq "TEXT");
      $document_element_boundary = $responses->get("IMAGE_BOUNDARIES")->get("BY_KEY", $document_element_id) if($modality eq "IMAGE");
      $document_element_boundary = $responses->get("KEYFRAME_BOUNDARIES")->get("BY_KEY", $keyframe_id) if($modality eq "VIDEO");
      unless($document_element_boundary->validate($provenance)) {
        $logger->record_problem("SPAN_OFF_BOUNDARY", $provenance, $document_element_boundary->tostring(), $document_element_id, $where);
        return;
      }
      1;
    },
  },

  'VALUE_PROVENANCE_TRIPLES' => {
    NAME => 'VALUE_PROVENANCE_TRIPLES',
    VALIDATE => sub {
      my ($responses, $logger, $where, $queries, $schema, $column, $entry, $column_name) = @_;
      my $provenances = $entry->get($column_name);
      return 1 if($schema->{TASK} eq "task3" && $schema->{QUERY_TYPE} eq "GRAPH" && $provenances eq "NULL");
      if($provenances =~ /^;/ || $provenances =~ /;$/) {
        $logger->record_problem("INCORRECT_PROVENANCE_FORMAT", $provenances, $where);
        return;
      }
      my $num_provenances = split(";", $provenances);
      unless($num_provenances == 1 or $num_provenances == 2) {
        $logger->record_problem("UNEXPECTED_NUM_SPANS", $provenances, "1 or 2", $num_provenances, $where);
        return;
      }
      1;
    },
  },

);

my %normalizers = (
  'CONFIDENCE' => {
    NAME => 'CONFIDENCE',
    NORMALIZE => sub {
      my ($responses, $logger, $where, $queries, $schema, $entry, $column_name) = @_;
      my $original_value = $entry->get($column_name);
      my $value = $original_value;
      if ($value eq '1') {
        $logger->record_problem('MISSING_DECIMAL_POINT', $value, $where);
        $value = '1.0';
      }
      elsif($value =~ /^\d+\.\d+e[-+]?\d+$/i) {
        $logger->record_problem('IMPROPER_CONFIDENCE_VALUE', $value, $where);
        $value = sprintf("%.12f", $value);
      }
      $entry->set($column_name, $value);
    },
  },
  'IMPORTANCE' => {
    NAME => 'IMPORTANCE',
    NORMALIZE => sub {
      my ($responses, $logger, $where, $queries, $schema, $entry, $column_name) = @_;
      my $original_value = $entry->get($column_name);
      my $value = $original_value;
      if($value =~ /^\d+\.\d+e[-+]?\d+$/i) {
        $logger->record_problem('IMPROPER_IMPORTANCE_VALUE', $value, $where);
        $value = sprintf("%.12f", $value);
      }
      $entry->set($column_name, $value);
    },
  },
);

my %schemas = ( 
  '2019_TA1_CL_SUBMISSION' => {
    NAME => '2019_TA1_CL_SUBMISSION',
    YEAR => 2019,
    TASK => "task1",
    QUERY_TYPE => 'CLASS',
    FILE_TYPE => 'SUBMISSION',
    SAMPLES => ["D0100 <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LDCOntology#PER> <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LdcAnnotations#cluster-E0137> <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LDCOntology#PER.Combatant.Sniper> D0100:DE005_03:(210,60)-(310,210) 1.0E0 1.0E0 2.34E-1"],
    HEADER => [qw(?docid ?query_type ?cluster ?type ?infj_span ?t_cv ?cm_cv ?j_cv)],
    COLUMNS => [qw(
      DOCUMENT_ID
      QUERY_ENTITY_TYPE_IN_RESPONSE
      CLUSTER_ID
      MATCHING_ENTITY_TYPE_IN_RESPONSE
      VALUE_PROVENANCE_TRIPLE
      TYPE_CONFIDENCE
      CLUSTER_MEMBERSHIP_CONFIDENCE
      JUSTIFICATION_CONFIDENCE
    )],
  },

  '2019_TA1_GR_SUBMISSION' => {
    NAME => '2019_TA1_GR_SUBMISSION',
    YEAR => 2019,
    TASK => "task1",
    QUERY_TYPE => 'GRAPH',
    FILE_TYPE => 'SUBMISSION',
    SAMPLES => ["IC0011UQQ <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LDCOntology#Conflict.Attack.FirearmAttack_Attacker> <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LDCOntology#Conflict.Attack.FirearmAttack_Attacker> <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LdcAnnotations#cluster-E0137> <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LdcAnnotations#E0137-D0100> IC0011UQQ:HC000Q7P6:(45,0)-(55,0) <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LdcAnnotations#cluster-E0159> <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LdcAnnotations#E0159-D0100> IC0011UQQ:HC000Q7P6:(45,0)-(55,0),IC0011UQQ:IC0011UQU:(200,100)-(400,300) 2.34E-1 1.0E0 5.43E-1 1.0E0"],
    HEADER => [qw(?docid ?edge_type_q ?edge_type ?object_cluster ?objectmo ?oinf_j_span ?subject_cluster ?subjectmo ?ej_span ?oinf_j_cv ?obcm_cv ?edge_cj_cv ?sbcm_cv)], 
    COLUMNS => [qw(
      DOCUMENT_ID
      QUERY_EDGE_TYPE_IN_RESPONSE
      MATCHING_EDGE_TYPE_IN_RESPONSE
      OBJECT_CLUSTER_ID
      OBJECT_MEMBER
      OBJECT_VALUE_PROVENANCE_TRIPLE
      SUBJECT_CLUSTER_ID
      SUBJECT_MEMBER
      EDGE_PROVENANCE_TRIPLES
      OBJECT_INFORMATIVE_JUSTIFICATION_CONFIDENCE
      OBJECT_CLUSTER_MEMBERSHIP_CONFIDENCE
      EDGE_COMPOUND_JUSTIFICATION_CONFIDENCE
      SUBJECT_CLUSTER_MEMBERSHIP_CONFIDENCE
    )],
  },

  '2019_TA2_GR_SUBMISSION' => {
    NAME => '2019_TA2_GR_SUBMISSION',
    YEAR => 2019,
    TASK => "task2",
    QUERY_TYPE => 'GRAPH',
    FILE_TYPE => 'SUBMISSION',
    SAMPLES => ["IC0011UQQ <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LDCOntology#Conflict.Attack_Place> <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LDCOntology#Conflict.Attack.FirearmAttack_Place> LDC2018E80:703448|LDC2018E80:703449 LDC2018E80:703448 <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LdcAnnotations#cluster-E0124> <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LdcAnnotations#E0124-D0100> IC0011UQQ:HC000Q7P6:(45,0)-(55,0) <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LdcAnnotations#cluster-E0159> <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LdcAnnotations#E0159-D0100> IC0011UQQ:HC000Q7P6:(45,0)-(55,0),IC0011UQQ:IC0011UQU:(200,100)-(400,300) 1.98E-1 2.34E-1 1.0E0 5.43E-1 1.0E0"],
    HEADER => [qw(?docid ?edge_type_q ?edge_type ?olink_target_q ?olink_target ?object_cluster ?objectmo ?oinf_j_span ?subject_cluster ?subjectmo ?ej_span ?orfkblink_cv ?oinf_j_cv ?obcm_cv ?edge_cj_cv ?sbcm_cv)],
    COLUMNS => [qw(
      DOCUMENT_ID
      QUERY_EDGE_TYPE_IN_RESPONSE
      MATCHING_EDGE_TYPE_IN_RESPONSE
      QUERY_LINK_TARGET_IN_RESPONSE
      MATCHING_LINK_TARGET_IN_RESPONSE
      OBJECT_CLUSTER_ID
      OBJECT_MEMBER
      OBJECT_VALUE_PROVENANCE_TRIPLE
      SUBJECT_CLUSTER_ID
      SUBJECT_MEMBER
      EDGE_PROVENANCE_TRIPLES
      REFKB_LINK_CONFIDENCE
      OBJECT_INFORMATIVE_JUSTIFICATION_CONFIDENCE
      OBJECT_CLUSTER_MEMBERSHIP_CONFIDENCE
      EDGE_COMPOUND_JUSTIFICATION_CONFIDENCE
      SUBJECT_CLUSTER_MEMBERSHIP_CONFIDENCE
    )],
  },
  
  '2019_TA3_GR_SUBMISSION' => {
    NAME => '2019_TA3_GR_SUBMISSION',
    YEAR => 2019,
    TASK => "task3",
    QUERY_TYPE => 'GRAPH',
    FILE_TYPE => 'SUBMISSION',
    SAMPLES => ["IC0011UQQ <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LDCOntology#Conflict.Attack.FirearmAttack_Attacker> <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LdcAnnotations#cluster-E0137> <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LdcAnnotations#E0137-D0100> IC0011UQQ:HC000Q7P6:(45,0)-(55,0) <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LDCOntology#PER.Combatant.Sniper> <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LdcAnnotations#cluster-E0159> <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LdcAnnotations#E0159-D0100> NULL  <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LDCOntology#Conflict.Attack.FirearmAttack>  IC0011UQQ:HC000Q7P6:(45,0)-(55,0),IC0011UQQ:IC0011UQU:(200,100)-(400,300) 9.05E1  7.55E1  1.105E2 Sniper  5.43E-1"],
    HEADER => [qw(?docid ?edge_type ?object_cluster ?objectmo ?oinf_j_span ?object_type ?subject_cluster ?subjectmo ?sinf_j_span ?subject_type ?ej_span ?hypothesis_iv ?subjectc_iv ?edge_iv ?objectc_handle ?edge_cj_cv)],
    COLUMNS => [qw(
      DOCUMENT_ID
      EDGE_TYPE_IN_RESPONSE
      OBJECT_CLUSTER_ID
      OBJECT_MEMBER
      OBJECT_VALUE_PROVENANCE_TRIPLE
      OBJECT_TYPE
      SUBJECT_CLUSTER_ID
      SUBJECT_MEMBER
      SUBJECT_VALUE_PROVENANCE_TRIPLE
      SUBJECT_TYPE
      EDGE_PROVENANCE_TRIPLES
      HYPOTHESIS_IMPORTANCE_VALUE
      SUBJECT_CLUSTER_IMPORTANCE_VALUE
      EDGE_IMPORTANCE_VALUE
      OBJECT_HANDLE
      EDGE_COMPOUND_JUSTIFICATION_CONFIDENCE
    )],
  },

  '2019_TA2_ZH_SUBMISSION' => {
    NAME => '2019_TA2_ZH_SUBMISSION',
    YEAR => 2019,
    TASK => "task2",
    QUERY_TYPE => 'ZEROHOP',
    FILE_TYPE => 'SUBMISSION',
    SAMPLES => ["IC0011UQQ LDC2018E80:703448 LDC2018E80:703448 <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LdcAnnotations#cluster-E0124> IC0011UQQ:HC000Q7P6:(45,0)-(55,0) 2.34E-1 1.98E-1"],
    HEADER => [qw(?docid ?query_link_target  ?link_target  ?cluster  ?infj_span  ?j_cv ?link_cv)],
    COLUMNS => [qw(
      DOCUMENT_ID
      QUERY_LINK_TARGET_IN_RESPONSE
      MATCHING_LINK_TARGET_IN_RESPONSE
      CLUSTER_ID
      VALUE_PROVENANCE_TRIPLE
      JUSTIFICATION_CONFIDENCE
      REFKB_LINK_CONFIDENCE
    )],
  },
);

my %columns = (
  CLUSTER_ID => {
    NAME => 'CLUSTER_ID',
    DESCRIPTION => 'Cluster ID in response',
    YEARS => [2019],
    TASKS => ['task2'],
    QUERY_TYPES => ['ZEROHOP'],
    FILE_TYPES => ['SUBMISSION'],
  },

  CLUSTER_MEMBERSHIP_CONFIDENCE => {
    NAME => 'CLUSTER_MEMBERSHIP_CONFIDENCE',
    DESCRIPTION => "System confidence in entry, taken from submission",
    YEARS => [2019],
    TASKS => ['task1'],
    QUERY_TYPES => ['CLASS'],
    FILE_TYPES => ['SUBMISSION'],
    PATTERN => qr/\d+(?:\.\d+(e[-+]?\d\d)?)?/,
    NORMALIZE => 'CONFIDENCE',
    VALIDATE => 'CONFIDENCE',
  },

  DOCUMENT_ID => {
    NAME => 'DOCUMENT_ID',
    DESCRIPTION => "Document ID for provenance",
    YEARS => [2019],
    TASKS => ['task1','task2','task3'],
    QUERY_TYPES => ['CLASS','GRAPH','ZEROHOP'],
    FILE_TYPES => ['SUBMISSION'],
    PATTERN => $anything_pattern,
    VALIDATE => 'DOCUMENT_ID',
  },

  EDGE_COMPOUND_JUSTIFICATION_CONFIDENCE => {
    NAME => 'EDGE_COMPOUND_JUSTIFICATION_CONFIDENCE',
    DESCRIPTION => "System confidence in entry, taken from submission",
    YEARS => [2019],
    TASKS => ['task1','task2','task3'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    PATTERN => qr/\d+(?:\.\d+(e[-+]?\d\d)?)?/,
    NORMALIZE => 'CONFIDENCE',
    VALIDATE => 'CONFIDENCE',
  },

  EDGE_IMPORTANCE_VALUE => {
    NAME => 'EDGE_IMPORTANCE_VALUE',
    DESCRIPTION => "Edge importance value; taken from submission",
    YEARS => [2019],
    TASKS => ['task3'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    NORMALIZE => 'IMPORTANCE',
    VALIDATE => 'IMPORTANCE',
  },

  EDGE_PROVENANCE_TRIPLES => {
    NAME => 'EDGE_PROVENANCE_TRIPLES',
    DESCRIPTION => "Original string representation of the edge justification",
    YEARS => [2019],
    TASKS => ['task1','task2','task3'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    PATTERN => $provenance_triples_pattern,
    VALIDATE => 'VALUE_PROVENANCE_TRIPLES',
  },

  EDGE_PROVENANCE_TRIPLES_1 => {
    NAME => 'EDGE_PROVENANCE_TRIPLES_1',
    DESCRIPTION => "Original string representation of the edge justification",
    YEARS => [2019],
    TASKS => ['task1','task2'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    PATTERN => $provenance_triples_pattern,
    GENERATOR => sub {
      my ($responses, $logger, $where, $queries, $schema, $entry) = @_;
      my $triples = $entry->get("EDGE_PROVENANCE_TRIPLES_ARRAY");
      $entry->set("EDGE_PROVENANCE_TRIPLES_1", @$triples[0]);
    },
    VALIDATE => 'VALUE_PROVENANCE_TRIPLE',
    DEPENDENCIES => [qw(EDGE_PROVENANCE_TRIPLES_ARRAY)],
  },

  EDGE_PROVENANCE_TRIPLES_2 => {
    NAME => 'EDGE_PROVENANCE_TRIPLES_2',
    DESCRIPTION => "Original string representation of the edge justification",
    YEARS => [2019],
    TASKS => ['task1','task2'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    PATTERN => $provenance_triples_pattern,
    GENERATOR => sub {
      my ($responses, $logger, $where, $queries, $schema, $entry) = @_;
      my $triples = $entry->get("EDGE_PROVENANCE_TRIPLES_ARRAY");
      $entry->set("EDGE_PROVENANCE_TRIPLES_2", @$triples[1]) if @$triples > 1;
    },
    VALIDATE => 'VALUE_PROVENANCE_TRIPLE',
    OPTIONAL => 1,
    DEPENDENCIES => [qw(EDGE_PROVENANCE_TRIPLES_ARRAY)],
  },

  EDGE_PROVENANCE_TRIPLES_ARRAY => {
    NAME => 'EDGE_PROVENANCE_TRIPLES_ARRAY',
    DESCRIPTION => "Original string representation of the edge justification",
    YEARS => [2019],
    TASKS => ['task1','task2'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    PATTERN => $provenance_triples_pattern,
    GENERATOR => sub {
      my ($responses, $logger, $where, $queries, $schema, $entry) = @_;
      my $triples = $entry->get("EDGE_PROVENANCE_TRIPLES");
      my @triples = split(/;/, $triples);
      $entry->set("EDGE_PROVENANCE_TRIPLES_ARRAY", \@triples);
    },
    OPTIONAL => 1,
    DEPENDENCIES => [qw(EDGE_PROVENANCE_TRIPLES)],
  },

  EDGE_TYPE_IN_RESPONSE => {
    NAME => 'EDGE_TYPE_IN_RESPONSE',
    YEARS => [2019],
    TASKS => ['task3'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
  },

  FILENAME => {
    NAME => 'FILENAME',
    YEARS => [2019],
    TASKS => ['task1','task2'],
    QUERY_TYPES => ['CLASS','GRAPH','ZEROHOP'],
    FILE_TYPES => ['SUBMISSION'],
    DESCRIPTION => "The name of the file from which the description of the entry was read; added by load",
  },

  HYPOTHESIS_IMPORTANCE_VALUE => {
    NAME => 'HYPOTHESIS_IMPORTANCE_VALUE',
    YEARS => [2019],
    TASKS => ['task3'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    NORMALIZE => 'IMPORTANCE',
    VALIDATE => 'IMPORTANCE',
  },

  JUSTIFICATION_CONFIDENCE => {
    NAME => 'JUSTIFICATION_CONFIDENCE',
    DESCRIPTION => "System confidence in entry, taken from submission",
    YEARS => [2019],
    TASKS => ['task1','task2'],
    QUERY_TYPES => ['CLASS', 'ZEROHOP'],
    FILE_TYPES => ['SUBMISSION'],
    PATTERN => qr/\d+(?:\.\d+(e[-+]?\d\d)?)?/,
    NORMALIZE => 'CONFIDENCE',
    VALIDATE => 'CONFIDENCE',
  },

  KB_DOCUMENT_ID => {
    NAME => 'KB_DOCUMENT_ID',
    DESCRIPTION => "DOCUMENT_ID from which the KB was build; required for task1 systems",
    YEARS => [2019],
    TASKS => ['task1'],
    QUERY_TYPES => ['CLASS','GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    GENERATOR => sub {
      my ($responses, $logger, $where, $queries, $schema, $entry) = @_;
      my $filename = $entry->get("FILENAME");
      my ($directory) = $filename =~ /\/(.*?)\.ttl\//;
      my @elements = split(/\//, $directory);
      my $kb_documentid = pop(@elements);
      $entry->set("KB_DOCUMENT_ID", $kb_documentid);
    },
    VALIDATE => 'KB_DOCUMENT_ID',
  },

  LINE => {
    NAME => 'LINE',
    DESCRIPTION => "the input line that generated this entry - added by load",
  },

  LINENUM => {
    NAME => 'LINENUM',
    DESCRIPTION => "The line number in FILENAME containing LINE - added by load",
  },

  MATCHING_EDGE_TYPE_IN_RESPONSE => {
    NAME => 'MATCHING_EDGE_TYPE_IN_RESPONSE',
    DESCRIPTION => "The type of edge in response",
    YEARS => [2019],
    TASKS => ['task1','task2'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    VALIDATE => 'MATCHING_EDGE_TYPE_IN_RESPONSE',
  },

  MATCHING_ENTITY_TYPE_IN_RESPONSE => {
    NAME => 'MATCHING_ENTITY_TYPE_IN_RESPONSE',
    DESCRIPTION => "The type of entity in response",
    YEARS => [2019],
    TASKS => ['task1'],
    QUERY_TYPES => ['CLASS'],
    FILE_TYPES => ['SUBMISSION'],
    VALIDATE => 'MATCHING_ENTITY_TYPE_IN_RESPONSE',
  },

  MATCHING_LINK_TARGET_IN_RESPONSE => {
    NAME => 'MATCHING_LINK_TARGET_IN_RESPONSE',
    YEARS => [2019],
    TASKS => ['task2'],
    QUERY_TYPES => ['ZEROHOP','GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    DESCRIPTION => "The matching link target of the cluster in response",
    VALIDATE => 'MATCHING_LINK_TARGET_IN_RESPONSE',
  },

  OBJECT_CLUSTER_ID => {
    NAME => 'OBJECT_CLUSTER_ID',
    DESCRIPTION => 'Object cluster ID in response',
    YEARS => [2019],
    TASKS => ['task1','task2','task3'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
  },

  OBJECT_CLUSTER_MEMBERSHIP_CONFIDENCE => {
    NAME => 'OBJECT_CLUSTER_MEMBERSHIP_CONFIDENCE',
    DESCRIPTION => "System confidence in entry, taken from submission",
    YEARS => [2019],
    TASKS => ['task1','task2'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    PATTERN => qr/\d+(?:\.\d+(e[-+]?\d\d)?)?/,
    NORMALIZE => 'CONFIDENCE',
    VALIDATE => 'CONFIDENCE',
  },

  OBJECT_HANDLE => {
    NAME => 'OBJECT_HANDLE',
    DESCRIPTION => 'Natural lanugage handle of the object of the edge, taken from response',
    YEARS => [2019],
    TASKS => ['task3'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
  },

  OBJECT_INFORMATIVE_JUSTIFICATION_CONFIDENCE => {
    NAME => 'OBJECT_INFORMATIVE_JUSTIFICATION_CONFIDENCE',
    DESCRIPTION => "System confidence in entry, taken from submission",
    YEARS => [2019],
    TASKS => ['task1','task2'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    PATTERN => qr/\d+(?:\.\d+(e[-+]?\d\d)?)?/,
    NORMALIZE => 'CONFIDENCE',
    VALIDATE => 'CONFIDENCE',
  },

  OBJECT_MEMBER => {
    NAME => 'OBJECT_MEMBER',
    DESCRIPTION => 'Member of the object cluster in response',
    YEARS => [2019],
    TASKS => ['task1','task2'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
  },

  OBJECT_TYPE => {
    NAME => 'OBJECT_TYPE',
    DESCRIPTION => 'Type of the object of the edge, taken from response',
    YEARS => [2019],
    TASKS => ['task3'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
  },

  OBJECT_VALUE_PROVENANCE_TRIPLE => {
    NAME => 'OBJECT_VALUE_PROVENANCE_TRIPLE',
    DESCRIPTION => "Original string representation of object's VALUE_PROVENANCE",
    YEARS => [2019],
    TASKS => ['task1','task2','task3'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    PATTERN => $provenance_triple_pattern,
    VALIDATE => 'VALUE_PROVENANCE_TRIPLE',
  },

  QUERY => {
    NAME => 'LINENUM',
    DESCRIPTION => "A pointer to the appropriate query structure",
    YEARS => [2019],
    TASKS => ['task1','task2','task3'],
    QUERY_TYPES => ['CLASS','GRAPH','ZEROHOP'],
    FILE_TYPES => ['SUBMISSION'],
    GENERATOR => sub {
      my ($responses, $logger, $where, $queries, $schema, $entry) = @_;
      my $query = $queries->get("QUERY", $entry->get("QUERY_ID"));
      $entry->set("QUERY", $query);
    },
    DEPENDENCIES => [qw(QUERY_ID)],
  },

  QUERY_EDGE_TYPE_IN_RESPONSE => {
    NAME => 'QUERY_EDGE_TYPE_IN_RESPONSE',
    YEARS => [2019],
    TASKS => ['task1','task2'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    DESCRIPTION => "The type of edge as part of the query",
    VALIDATE => 'QUERY_EDGE_TYPE_IN_RESPONSE',
  },

  QUERY_ENTITY_TYPE_IN_RESPONSE => {
    NAME => 'QUERY_ENTITY_TYPE_IN_RESPONSE',
    YEARS => [2019],
    TASKS => ['task1'],
    QUERY_TYPES => ['CLASS'],
    FILE_TYPES => ['SUBMISSION'],
    DESCRIPTION => "The type of entity as part of the query",
    VALIDATE => 'QUERY_ENTITY_TYPE_IN_RESPONSE',
  },

  QUERY_ID => {
    NAME => 'QUERY_ID',
    DESCRIPTION => "Query ID of query this entry is responding to.",
    YEARS => [2019],
    TASKS => ['task1','task2','task3'],
    QUERY_TYPES => ['CLASS','GRAPH','ZEROHOP'],
    FILE_TYPES => ['SUBMISSION'],
    GENERATOR => sub {
      my ($responses, $logger, $where, $queries, $schema, $entry) = @_;
      # recover the queryid from the filename
      my $query_id = $entry->get("FILENAME");
      $query_id =~ s/^(.*?\/)+//g;
      $query_id =~ s/\.rq\.tsv//;
      $entry->set("QUERY_ID", $query_id);
    },
    PATTERN => $anything_pattern,
    REQUIRED => 'ALL',
  },

  QUERY_LINK_TARGET_IN_RESPONSE => {
    NAME => 'QUERY_LINK_TARGET_IN_RESPONSE',
    YEARS => [2019],
    TASKS => ['task2'],
    QUERY_TYPES => ['ZEROHOP','GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    DESCRIPTION => "The link target as part of the query",
    VALIDATE => 'QUERY_LINK_TARGET_IN_RESPONSE',
  },

  REFKB_LINK_CONFIDENCE => {
    NAME => 'REFKB_LINK_CONFIDENCE',
    DESCRIPTION => "Confidence of linking the cluster to reference KB, taken from submission",
    YEARS => [2019],
    TASKS => ['task2'],
    QUERY_TYPES => ['ZEROHOP','GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    PATTERN => qr/\d+(?:\.\d+(e[-+]?\d\d)?)?/,
    NORMALIZE => 'CONFIDENCE',
    VALIDATE => 'CONFIDENCE',
  },

  RUN_ID => {
    NAME => 'RUN_ID',
    DESCRIPTION => "Run ID for this entry",
    YEARS => [2019],
    TASKS => ['task1','task2','task3'],
    QUERY_TYPES => ['CLASS','GRAPH','ZEROHOP'],
    FILE_TYPES => ['SUBMISSION'],
    PATTERN => $anything_pattern,
  },

  SUBJECT_CLUSTER_ID => {
    NAME => 'SUBJECT_CLUSTER_ID',
    DESCRIPTION => 'Subject cluster ID in response',
    YEARS => [2019],
    TASKS => ['task1','task2','task3'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
  },

  SUBJECT_CLUSTER_IMPORTANCE_VALUE => {
    NAME => 'SUBJECT_CLUSTER_IMPORTANCE_VALUE',
    YEARS => [2019],
    TASKS => ['task3'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    NORMALIZE => 'IMPORTANCE',
    VALIDATE => 'IMPORTANCE',
  },

  SUBJECT_CLUSTER_MEMBERSHIP_CONFIDENCE => {
    NAME => 'SUBJECT_CLUSTER_MEMBERSHIP_CONFIDENCE',
    DESCRIPTION => "System confidence in entry, taken from submission",
    YEARS => [2019],
    TASKS => ['task1','task2'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    PATTERN => qr/\d+(?:\.\d+(e[-+]?\d\d)?)?/,
    NORMALIZE => 'CONFIDENCE',
    VALIDATE => 'CONFIDENCE',
  },

  SUBJECT_MEMBER => {
    NAME => 'SUBJECT_MEMBER',
    DESCRIPTION => 'Member of the subject cluster in response',
    YEARS => [2019],
    TASKS => ['task1','task2','task3'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
  },

  SUBJECT_TYPE => {
    NAME => 'SUBJECT_TYPE',
    DESCRIPTION => 'Type of the subject of the edge, taken from response',
    YEARS => [2019],
    TASKS => ['task3'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    VALIDATE => 'SUBJECT_TYPE',
  },

  SUBJECT_VALUE_PROVENANCE_TRIPLE => {
    NAME => 'SUBJECT_VALUE_PROVENANCE_TRIPLE',
    DESCRIPTION => "Original string representation of subject's VALUE_PROVENANCE",
    YEARS => [2019],
    TASKS => ['task3'],
    QUERY_TYPES => ['GRAPH'],
    FILE_TYPES => ['SUBMISSION'],
    PATTERN => $provenance_triple_pattern,
    VALIDATE => 'VALUE_PROVENANCE_TRIPLE',
  },

  TYPE_CONFIDENCE => {
    NAME => 'TYPE_CONFIDENCE',
    DESCRIPTION => "System confidence in entry, taken from submission",
    YEARS => [2019],
    TASKS => ['task1'],
    QUERY_TYPES => ['CLASS'],
    FILE_TYPES => ['SUBMISSION'],
    PATTERN => qr/\d+(?:\.\d+(e[-+]?\d\d)?)?/,
    NORMALIZE => 'CONFIDENCE',
    VALIDATE => 'CONFIDENCE',
  },

  VALUE_PROVENANCE_TRIPLE => {
    NAME => 'VALUE_PROVENANCE_TRIPLE',
    DESCRIPTION => "Original string representation of VALUE_PROVENANCE",
    YEARS => [2019],
    TASKS => ['task1','task2'],
    QUERY_TYPES => ['CLASS','ZEROHOP'],
    FILE_TYPES => ['SUBMISSION'],
    PATTERN => $provenance_triple_pattern,
    VALIDATE => 'VALUE_PROVENANCE_TRIPLE',
  },

  YEAR => {
    NAME => 'YEAR',
    DESCRIPTION => "Year",
    YEARS => [2019],
    TASKS => ['task1','task2'],
    QUERY_TYPES => ['CLASS','GRAPH','ZEROHOP'],
    FILE_TYPES => ['SUBMISSION'],
  },

);

sub new {
  my ($class, $logger, $queries, $docid_mappings, $text_document_boundaries, 
    $images_boundingboxes, $keyframes_boundingboxes, $runs_dir, $runs_to_load, $queries_to_load, $cas_dir) = @_;
  my $self = {
    __CLASS__ => 'ResponseSet',
    QUERIES => $queries,
    DOCID_MAPPINGS => $docid_mappings,
    TEXT_BOUNDARIES => $text_document_boundaries,
    IMAGE_BOUNDARIES => $images_boundingboxes, 
    KEYFRAME_BOUNDARIES => $keyframes_boundingboxes,
    RESPONSES => Container->new($logger, "Response"),
    CATEGORIZED_RESPONSES => Container->new($logger, "Container"),
    CLUSTER_TYPES => Container->new($logger),
    RUNS_DIR => $runs_dir,
    CAS_DIR => $cas_dir,
    RUNS_TO_LOAD => $runs_to_load,
    QUERIES_TO_LOAD => $queries_to_load,
    LOGGER => $logger,
  };
  bless($self, $class);
  foreach my $run_id($runs_to_load->toarray()) {
    print STDERR "--loading run: $run_id\n";
    my $run_dir = "$runs_dir/$run_id";
    my $ca_dir = "$cas_dir/$run_id" if $cas_dir;
    $logger->NIST_die("$run_dir does not exist") unless -e $run_dir;
    foreach my $input_subdir (<$run_dir/*>) {
      # skip if not a directory
      next unless -d $input_subdir;
      my $input_subdir_name = $input_subdir;
      $input_subdir_name =~ s/^$run_dir\///;
      # iterate through all response files
      foreach my $responses_filename(<$input_subdir/*.rq.tsv>) {
        my $query_id = $responses_filename;
        $query_id =~ s/^(.*?\/)+//g;
        $query_id =~ s/\.rq\.tsv//;
        my $ca_filename = "$ca_dir/$input_subdir_name/$query_id.rq.tsv" if $ca_dir;
        # skip if the query is unexpected
        unless ($queries->exists($query_id)) {
          $logger->record_debug_information("SKIPPING_INPUT_FILE", $responses_filename, {FILENAME => __FILE__, LINENUM => __LINE__});
          next;
        }
        # skip if the query is not to be included in the pool
        next unless $queries_to_load->exists($query_id);
        # proceed with loading the file
        my $schema_name = &identify_file_schema($logger, $responses_filename);
        my $schema = $schemas{$schema_name};
        unless ($schema) {
          $logger->record_problem('UNKNOWN_RESPONSE_FILE_TYPE', $responses_filename, 'NO_SOURCE');
          next;
        }
        $self->load_responses($logger, $queries, $responses_filename, $schema, $run_id);
        $self->load_aggregated_confidences($logger, $queries, $ca_filename, $schema, $run_id) if $ca_filename;
      }
    }
  }
  $self;
}

sub identify_file_schema {
  my ($logger, $filename) = @_;
  my $schema_name;
  my $query_id = $filename;
  $query_id =~ s/^(.*?\/)+//g;
  $query_id =~ s/\.rq\.tsv//;
  $schema_name = "2019_TA1_CL_SUBMISSION" if($query_id =~ /^AIDA_TA1_CL_2019_\d+$/);
  $schema_name = "2019_TA1_GR_SUBMISSION" if($query_id =~ /^AIDA_TA1_GR_2019_\d+$/);
  $schema_name = "2019_TA2_ZH_SUBMISSION" if($query_id =~ /^AIDA_TA2_ZH_2019_\d+$/);
  $schema_name = "2019_TA2_GR_SUBMISSION" if($query_id =~ /^AIDA_TA2_GR_2019_\d+$/);
  $schema_name = "2019_TA3_GR_SUBMISSION" if($query_id =~ /^AIDA_TA3_GR_2019_\d+$/);
  $schema_name;
}

sub load_responses {
  my ($self, $logger, $queries, $filename, $schema, $runid) = @_;
  my $docid_mappings = $self->get("DOCID_MAPPINGS");
  my $filehandler = FileHandler->new($logger, $filename);
  # verify if the number of columns in the header are as expected
  my @provided_header = @{$filehandler->get("HEADER")->get("ELEMENTS")};
  my @expected_header = @{$schema->{HEADER}};
  if (@provided_header != @expected_header) {
    $logger->record_problem("UNEXPECTED_COLUMN_NUM", $#expected_header, $#provided_header, {FILENAME=>$filename, LINENUM=>1});
    return;
  }
  # verify if the column names in the header are as expected
  for(my $i=0; $i<=$#provided_header; $i++) {
    if($provided_header[$i] ne $expected_header[$i]) {
      $logger->record_problem("UNEXPECTED_COLUMN_HEADER", $i+1, $expected_header[$i], $provided_header[$i], {FILENAME=>$filename, LINENUM=>1});
      return;
    }
  }
  
  my @entries = $filehandler->get("ENTRIES")->toarray();
  foreach my $entry(@entries) {
    my $linenum = $entry->get("LINENUM");
    my @provided_columns = split(/\t/, $entry->get("LINE"));
    if(@provided_columns != @expected_header) {
      $logger->record_problem("UNEXPECTED_COLUMN_NUM", $#expected_header, $#provided_columns, $entry->get("WHERE"));
      return;
    }
    $entry->set("RUN_ID", $runid);
    $entry->set("FILENAME", $filename);
    for(my $i=0; $i<=$#expected_header; $i++) {
      $entry->set(@{$schema->{COLUMNS}}[$i], $entry->get(@{$schema->{HEADER}}[$i]))
        if defined $entry->get(@{$schema->{HEADER}}[$i]);
    }
    $entry->set("SCHEMA", $schema);
    foreach my $column_name(keys %columns) {
      my $column = $columns{$column_name};
      # skip the column if the it is not required for the given year, task and query_type
      next unless $self->column_required($column, $schema);
      # this is a required column
      # generate this column if a generator is provided, 
      # otherwise mark the entry as invalid and move on to the next column
      $self->generate_slot($logger, $entry->get("WHERE"), $queries, $schema, $entry, $column_name);
      # normalize if normalizer is provided
      if($column->{NORMALIZE}) {
        &{$normalizers{$column->{NORMALIZE}}->{NORMALIZE}}($self, $logger, $entry->get("WHERE"), $queries, $schema, $entry, $column_name);
      }
    }
    my $valid = 1;
    foreach my $column_name(keys %columns) {
      my $column = $columns{$column_name};
      # skip the column if the it is not required for the given year, task and query_type
      next unless $self->column_required($column, $schema);
      # validate the column, if a validator is provided
      if($column->{VALIDATE}) {
        if($validators{$column->{VALIDATE}}) {
          $valid = 0
            unless &{$validators{$column->{VALIDATE}}->{VALIDATE}}($self, $logger, $entry->get("WHERE"), $queries, $schema, $column, $entry, $column_name);
        }
        else {
          $logger->NIST_die("VALIDATOR subroutine missing for $column_name");
        }
      }
    }
    $entry->set("VALID", $valid);
    $self->get("RESPONSES")->add($entry, "$filename:$linenum");
    my $code = $queries->get("TASK_AND_TYPE_CODE");
    if($code eq "TA1_CL") {
      my $query_id = $entry->get("QUERY_ID");
      my $kb_documentid = $entry->get("KB_DOCUMENT_ID");
      my $cluster_id = $entry->get("CLUSTER_ID");
      my $response_category = join("::", ($runid, $query_id, $kb_documentid, $cluster_id));
      $self->get("CATEGORIZED_RESPONSES")->get("BY_KEY", $response_category)->add($entry, "$filename:$linenum");
    }
    elsif($code eq "TA1_GR" || $code eq "TA2_GR") {
      my $uuid = main::generate_uuid_from_string($entry->get("LINE"));
      $logger->NIST_die("duplicate line: " . $entry->get("LINE")) if $self->get("CATEGORIZED_RESPONSES")->exists($uuid);
      $self->get("CATEGORIZED_RESPONSES")->add($entry, $uuid);
    }
  }
}

sub load_aggregated_confidences {
  my ($self, $logger, $queries, $ca_filename, $schema, $run_id) = @_;
  my $code = $queries->get("TASK_AND_TYPE_CODE");
  my $method = $self->can("load_aggregated_confidences_$code");
  $logger->NIST_die("ResponseSet->load_aggregated_confidences_$code() not found")
    unless $method;
  $method->($self, $logger, $queries, $ca_filename, $schema, $run_id);
}

sub load_aggregated_confidences_TA1_CL {
  my ($self, $logger, $queries, $ca_filename, $schema, $run_id) = @_;
  my @elements = split(/\//, $ca_filename);
  my $query_id = pop @elements;
  $query_id =~ s/^(.*?\/)+//g;
  $query_id =~ s/\.rq\.tsv//;
  my $kb_docid = pop @elements;
  $kb_docid =~ s/\.ttl$//;
  my $run_id_from_filename = pop @elements;
  foreach my $entry(FileHandler->new($logger, $ca_filename)->get("ENTRIES")->toarray()) {
    my $cluster_id = $entry->get("?cluster");
    my $rank = $entry->get("?rank");
    $self->add_cluster_rank_to_responses($logger, "TA1_CL", $cluster_id, $rank, $query_id, $kb_docid, $run_id, $entry->get("WHERE"));
  }
}

sub load_aggregated_confidences_TA2_ZH {
  my ($self, $logger, $queries, $ca_filename, $schema, $run_id) = @_;
  my @elements = split(/\//, $ca_filename);
  my $query_id = pop @elements;
  $query_id =~ s/^(.*?\/)+//g;
  $query_id =~ s/\.rq\.tsv//;
  my $kb_docid = pop @elements;
  $kb_docid =~ s/\.ttl$//;
  my $run_id_from_filename = pop @elements;
  foreach my $entry(FileHandler->new($logger, $ca_filename)->get("ENTRIES")->toarray()) {
    my $cluster_id = $entry->get("?cluster");
    my $rank = $entry->get("?rank");
    $self->add_cluster_rank_to_responses($logger, "TA2_ZH", $cluster_id, $rank, $query_id, undef, $run_id, $entry->get("WHERE"));
  }
}

sub load_aggregated_confidences_TA1_GR {
  my ($self, $logger, $queries, $ca_filename, $schema, $run_id) = @_;
  my @elements = split(/\//, $ca_filename);
  my $query_id = pop @elements;
  $query_id =~ s/^(.*?\/)+//g;
  $query_id =~ s/\.rq\.tsv//;
  my $kb_docid = pop @elements;
  $kb_docid =~ s/\.ttl$//;
  my $run_id_from_filename = pop @elements;
  foreach my $entry(FileHandler->new($logger, $ca_filename)->get("ENTRIES")->toarray()) {
    my @elements = split(/\t/, $entry->get("LINE"));
    my $rank = pop @elements;
    my $ag_cv = pop @elements;
    my $uuid = main::generate_uuid_from_string(join("\t", @elements));
    $logger->NIST_die("Following line in confidence aggregation file does not have a corresponding line in response file: \n" . $entry->get("LINE"))
      unless($self->get("CATEGORIZED_RESPONSES")->exists($uuid));
    my $response = $self->get("CATEGORIZED_RESPONSES")->get("BY_KEY", $uuid);
    $response->set("RANK", $rank);
    $response->set("AG_CV", $ag_cv);
  }
}

sub load_aggregated_confidences_TA2_GR {
  my ($self, $logger, $queries, $ca_filename, $schema, $run_id) = @_;
  my @elements = split(/\//, $ca_filename);
  my $query_id = pop @elements;
  $query_id =~ s/^(.*?\/)+//g;
  $query_id =~ s/\.rq\.tsv//;
  my $kb_docid = pop @elements;
  $kb_docid =~ s/\.ttl$//;
  my $run_id_from_filename = pop @elements;
  foreach my $entry(FileHandler->new($logger, $ca_filename)->get("ENTRIES")->toarray()) {
    my @elements = split(/\t/, $entry->get("LINE"));
    my $rank = pop @elements;
    my $ag_cv = pop @elements;
    my $uuid = main::generate_uuid_from_string(join("\t", @elements));
    $logger->NIST_die("Following line in confidence aggregation file does not have a corresponding line in response file: \n" . $entry->get("LINE"))
      unless($self->get("CATEGORIZED_RESPONSES")->exists($uuid));
    my $response = $self->get("CATEGORIZED_RESPONSES")->get("BY_KEY", $uuid);
    $response->set("RANK", $rank);
    $response->set("AG_CV", $ag_cv);
  }
}

sub add_cluster_rank_to_responses {
  my ($self, $logger, $code, $cluster_id, $rank, $query_id, $kb_docid, $run_id, $where) = @_;
  my $method = $self->can("add_cluster_rank_to_responses_$code");
  $logger->NIST_die("ResponseSet->add_cluster_rank_to_responses_$code() not found")
    unless $method;
  $method->($self, $logger, $cluster_id, $rank, $query_id, $kb_docid, $run_id, $where);
}

sub add_cluster_rank_to_responses_TA1_CL {
  my ($self, $logger, $cluster_id, $rank, $query_id, $kb_docid, $run_id, $where) = @_;
  my $response_category = join("::", ($run_id, $query_id, $kb_docid, $cluster_id));
  my @responses = $self->get("CATEGORIZED_RESPONSES")->get("BY_KEY", $response_category)->toarray();
  $logger->NIST_die("No matching response available to add cluster rank")
    unless @responses;
  foreach my $response(@responses) {
    $logger->NIST_die("Rank already exists for cluster in response: " . $response->get("LINE"))
      if $response->get("CLUSTER_RANK");
    $response->set("CLUSTER_RANK", $rank);
  }
}

sub add_cluster_rank_to_responses_TA2_ZH {
  my ($self, $logger, $cluster_id, $rank, $query_id, $undef0, $run_id, $where) = @_;
  my @responses = grep {$_->get("CLUSTER_ID") eq $cluster_id &&
                                 $_->get("QUERY_ID") eq $query_id &&
                                 $_->get("RUN_ID") eq $run_id}
                  $self->get("RESPONSES")->toarray();
  $logger->NIST_die("No matching response available to add cluster rank")
    unless @responses;
  foreach my $response(@responses) {
    $logger->NIST_die("Rank already exists for cluster in response: " . $response->get("LINE"))
      if $response->get("CLUSTER_RANK");
    $response->set("CLUSTER_RANK", $rank);
  }
}

sub generate_slot {
  my ($self, $logger, $where, $queries, $schema, $entry, $column) = @_;
  return if $entry->get($column);
  my $spec = $columns{$column};
  $logger->NIST_die("No information available for $column column") unless defined $spec;
  my $dependencies = $spec->{DEPENDENCIES};
  if (defined $dependencies) {
    foreach my $dependency (@{$dependencies}) {
      $self->generate_slot($logger, $where, $queries, $schema, $entry, $dependency);
    }
  }
  my $generator = $spec->{GENERATOR};
  if (defined $generator) {
    &{$generator}($self, $logger, $where, $queries, $schema, $entry);
  }
}

sub get_AG_CV {
  my ($self, $response, $ac_fields) = @_;
  my $ag_cv = 1.0;
  foreach my $ac_field(@$ac_fields) {
    $ag_cv *= $response->get($ac_field);
  }
  $ag_cv;
}

sub column_required {
  my ($self, $column, $schema) = @_;
  my $year = $schema->{YEAR};
  my $task = $schema->{TASK};
  my $query_type = $schema->{QUERY_TYPE};
  my $file_type = $schema->{FILE_TYPE};
  return unless grep {$year eq $_} @{$column->{YEARS}};
  return unless grep {$task eq $_} @{$column->{TASKS}};
  return unless grep {$query_type eq $_} @{$column->{QUERY_TYPES}};
  return 1;
}

sub write_valid_output {
  my ($self, $output_dir) = @_;
  my $logger = $self->get("LOGGER");
  my %responses;
  foreach my $response($self->get("RESPONSES")->toarray()) {
    next unless $response->get("VALID");
    my $response_file = $response->get("FILENAME");
    my @elements = split(/\//, $response_file);
    my $filename = pop(@elements);
    my $kb_filename = pop(@elements);
    my $input_dir = join("/", @elements);
    my $output_file = "$output_dir/$kb_filename/$filename";
    system("mkdir -p $output_dir/$kb_filename");
    $responses{$output_file}{$response->get("LINENUM")} = $response;
  }
  foreach my $output_file(keys %responses) {
    $logger->NIST_die("$output_file already exists") if -e $output_file;
    my $header = 0;
    open(my $program_output, ">:utf8", $output_file) or $logger->NIST_die("Could not open $output_file: $!");
    foreach my $line_num(sort {$a<=>$b} keys %{$responses{$output_file}}) {
      my $response = $responses{$output_file}{$line_num};
      unless($header) {
        print $program_output $response->get("HEADER")->get("LINE"), "\n";
        $header = 1;
      }
      my $line = join("\t", map {$response->get($_)} @{$response->get("SCHEMA")->{COLUMNS}});
      print $program_output "$line\n";
    }
    close($program_output);
  }
}

#####################################################################################
# Pool
#####################################################################################

package Pool;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $task_and_type_code, $filename) = @_;
  my $self = $class->SUPER::new($logger, 'Kit');
  $self->{__CLASS__} = 'Pool';
  $self->{TASK_AND_TYPE_CODE} = $task_and_type_code;
  $self->{FILENAME} = $filename;
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self->load($task_and_type_code, $filename) if $filename;
  $self;
}

sub load {
  my ($self, $task_and_type_code, @arguments) = @_;
  my $method = $self->can("load_$task_and_type_code");
  $self->get("LOGGER")->NIST_die($self->{__CLASS__}."->load_$task_and_type_code() not found") unless $method;
  $method->($self, @arguments);
}

sub load_TA2_ZH {
  my ($self, $filename) = @_;
  my $logger = $self->get("LOGGER");
  my $filehandler = FileHandler->new($logger, $filename);
  my $header = $filehandler->get("HEADER");
  my $entries = $filehandler->get("ENTRIES");
  foreach my $entry($entries->toarray()) {
    my $query_id = $entry->get("KBID");
    my $kbid_kit = $self->get("BY_KEY", $query_id);

    my $kit_entry = KitEntry->new($logger);
    $kit_entry->set("HEADER", $header);
    map {$kit_entry->set($_, $entry->get($_))} @{$header->get("ELEMENTS")};

    my $uuid = &main::generate_uuid_from_string($kit_entry->tostring());
    $kbid_kit->add($kit_entry, $uuid) unless $self->exists($uuid);
  }
}

sub load_TA1_CL {
  my ($self, $filename) = @_;
  my $logger = $self->get("LOGGER");
  my $filehandler = FileHandler->new($logger, $filename);
  my $header = $filehandler->get("HEADER");
  my $entries = $filehandler->get("ENTRIES");
  foreach my $entry($entries->toarray()) {
    my $query_id = $entry->get("QUERY_ID");
    my $kbid_kit = $self->get("BY_KEY", $query_id);

    my $kit_entry = KitEntry->new($logger);
    $kit_entry->set("HEADER", $header);
    map {$kit_entry->set($_, $entry->get($_))} @{$header->get("ELEMENTS")};
    
    my $uuid = &main::generate_uuid_from_string($kit_entry->tostring());
    $kbid_kit->add($kit_entry, $uuid) unless $self->exists($uuid);
  }
}

sub load_TA1_GR {
  my ($self, $filename) = @_;
  my $logger = $self->get("LOGGER");
  my $filehandler = FileHandler->new($logger, $filename);
  my $header = $filehandler->get("HEADER");
  my $entries = $filehandler->get("ENTRIES");
  foreach my $entry($entries->toarray()) {
    my $kit_id = $entry->get("KIT_ID");
    my $kit = $self->get("BY_KEY", $kit_id);

    my $kit_entry = KitEntry->new($logger);
    $kit_entry->set("HEADER", $header);
    map {$kit_entry->set($_, $entry->get($_))} @{$header->get("ELEMENTS")};
    
    my $uuid = &main::generate_uuid_from_string($kit_entry->tostring());
    $kit->add($kit_entry, $uuid) unless $self->exists($uuid);
  }
}

sub load_TA2_GR {
  my ($self, $filename) = @_;
  $self->load_TA1_GR($filename);
}

#####################################################################################
# Kit
#####################################################################################

package Kit;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'KitEntry');
  $self->{__CLASS__} = 'Pool';
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
    __CLASS__ => 'KitEntry',
    TYPE => undef,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub tostring {
  my ($self) = @_;
  my @header = @{$self->get("HEADER")->get("ELEMENTS")};
  my @values = map {$self->get($_)} @header;
  join("\t", @values);
}

#####################################################################################
# ResponsesPool
#####################################################################################

package ResponsesPool;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $docid_mappings, $text_document_boundaries, $images_boundingboxes, $keyframes_boundingboxes, $previous_pool, $coredocs, $queries, $queries_to_load, $runs_to_load, $runs_dir, $cas_dir) = @_;
  my $self = {
    __CLASS__ => 'ResponsesPool',
    CONFIDENCE_AGGREGATION_DIR => $cas_dir,
    COREDOCS => $coredocs,
    DOCID_MAPPINGS => $docid_mappings,
    IMAGE_BOUNDARIES => $images_boundingboxes, 
    KEYFRAME_BOUNDARIES => $keyframes_boundingboxes,
    PREVIOUS_POOL => $previous_pool,
    QUERIES => $queries,
    QUERIES_TO_LOAD => $queries_to_load,
    RUNS_TO_LOAD => $runs_to_load,
    RUNS_DIR => $runs_dir, 
    TEXT_BOUNDARIES => $text_document_boundaries,
    RESPONSES_POOL => undef,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load();
  $self;
}

sub load {
  my ($self) = @_;
  my $cas_dir = $self->get("CONFIDENCE_AGGREGATION_DIR");
  my $coredocs = $self->get("COREDOCS");
  my $docid_mappings = $self->get("DOCID_MAPPINGS");
  my $images_boundingboxes = $self->get("IMAGE_BOUNDARIES");
  my $keyframes_boundingboxes = $self->get("KEYFRAME_BOUNDARIES");
  my $previous_pool = $self->get("PREVIOUS_POOL");
  my $queries = $self->get("QUERIES");
  my $queries_to_load = $self->get("QUERIES_TO_LOAD");
  my $queries_task_and_type = $queries->get("TASK_AND_TYPE_CODE");
  my $runs_to_load = $self->get("RUNS_TO_LOAD");
  my $runs_dir = $self->get("RUNS_DIR");
  my $text_document_boundaries = $self->get("TEXT_BOUNDARIES");
  my $logger = $self->get("LOGGER");
  my $responses_pool;
  $responses_pool = TA1ClassResponsesPool->new($logger, $docid_mappings, $text_document_boundaries, $images_boundingboxes, $keyframes_boundingboxes, $previous_pool, $coredocs, $queries, $queries_to_load, $runs_to_load, $runs_dir, $cas_dir) if($queries_task_and_type eq "TA1_CL");
  $responses_pool = TA1GraphResponsesPool->new($logger, $docid_mappings, $text_document_boundaries, $images_boundingboxes, $keyframes_boundingboxes, $previous_pool, $coredocs, $queries, $queries_to_load, $runs_to_load, $runs_dir, $cas_dir) if($queries_task_and_type eq "TA1_GR");
  $responses_pool = TA2ZeroHopResponsesPool->new($logger, $docid_mappings, $text_document_boundaries, $images_boundingboxes, $keyframes_boundingboxes, $previous_pool, $coredocs, $queries, $queries_to_load, $runs_to_load, $runs_dir, $cas_dir) if($queries_task_and_type eq "TA2_ZH");
  $responses_pool = TA2GraphResponsesPool->new($logger, $docid_mappings, $text_document_boundaries, $images_boundingboxes, $keyframes_boundingboxes, $previous_pool, $coredocs, $queries, $queries_to_load, $runs_to_load, $runs_dir, $cas_dir) if($queries_task_and_type eq "TA2_GR");
  $self->set("RESPONSES_POOL", $responses_pool);
}

sub tostring {
  my ($self) = @_;
  $self->get("RESPONSES_POOL")->tostring();
}

#####################################################################################
# TA1ClassResponsesPool
#####################################################################################

package TA1ClassResponsesPool;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $docid_mappings, $text_document_boundaries, $images_boundingboxes, $keyframes_boundingboxes, $previous_pool, $coredocs, $queries, $queries_to_load, $runs_to_load, $runs_dir, $cas_dir) = @_;
  my $self = {
    __CLASS__ => 'TA1ClassResponsesPool',
    CONFIDENCE_AGGREGATION_DIR => $cas_dir,
    COREDOCS => $coredocs,
    DOCID_MAPPINGS => $docid_mappings,
    IMAGE_BOUNDARIES => $images_boundingboxes, 
    KEYFRAME_BOUNDARIES => $keyframes_boundingboxes,
    PREVIOUS_POOL => $previous_pool,
    QUERIES => $queries,
    QUERIES_TO_LOAD => $queries_to_load,
    RUNS_TO_LOAD => $runs_to_load,
    RUNS_DIR => $runs_dir, 
    TEXT_BOUNDARIES => $text_document_boundaries,
    DELTA_POOL => undef,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load();
  $self;
}

sub load {
  my ($self) = @_;
  my $cas_dir = $self->get("CONFIDENCE_AGGREGATION_DIR");
  my $coredocs = $self->get("COREDOCS");
  my $docid_mappings = $self->get("DOCID_MAPPINGS");
  my $images_boundingboxes = $self->get("IMAGE_BOUNDARIES");
  my $keyframes_boundingboxes = $self->get("KEYFRAME_BOUNDARIES");
  my $queries = $self->get("QUERIES");
  my $queries_to_load = $self->get("QUERIES_TO_LOAD");
  my $queries_task_and_type = $queries->get("TASK_AND_TYPE_CODE");
  my $runs_to_load = $self->get("RUNS_TO_LOAD");
  my $runs_dir = $self->get("RUNS_DIR");
  my $text_document_boundaries = $self->get("TEXT_BOUNDARIES");
  my $logger = $self->get("LOGGER");
  my $responses_pool;

  my $responses = ResponseSet->new($logger,
                      $queries, 
                      $docid_mappings, 
                      $text_document_boundaries, 
                      $images_boundingboxes, 
                      $keyframes_boundingboxes,
                      $runs_dir,
                      $runs_to_load,
                      $queries_to_load,
                      $cas_dir);

  $self->generate_pool($responses);
}

sub generate_pool {
  my ($self, $responses) = @_;
  my $logger = $self->get("LOGGER");
  my $coredocs = $self->get("COREDOCS");
  my $pool = Pool->new($logger, "TA1_CL");
  my $previous_pool = $self->get("PREVIOUS_POOL");
  my $header_line = join("\t", qw(QUERY_ID CLASS ID MODALITY DOCID SPAN CORRECTNESS TYPE FQEC));
  my $header = Header->new($logger, $header_line);
  my $concat_key = ":";
  
  # select the clusters to be pooled
  my %clusters;
  foreach my $response($responses->get("RESPONSES")->toarray()) {
    my $query_id = $response->get("QUERY_ID");
    my $doc_id = $response->get("DOCUMENT_ID");
    next unless $coredocs->exists($doc_id);
    my $cluster_id = $response->get("CLUSTER_ID");
    my $run_id = $response->get("RUN_ID");
    my $cluster_rank = $response->get("CLUSTER_RANK");
    my $run_and_query_and_document = join($concat_key, ($run_id, $query_id, $doc_id));
    $clusters{$run_and_query_and_document}{RANKED}{$cluster_id} = $cluster_rank;
  }
  foreach my $run_and_query_and_document (keys %clusters) {
    my (undef, $query_id, undef) = split($concat_key, $run_and_query_and_document);
    my $max_num_of_clusters_per_document = $self->get("QUERIES_TO_LOAD")->get("BY_KEY", $query_id)->get("max_num_clusters");
    foreach my $cluster_id(sort {$clusters{$run_and_query_and_document}{RANKED}{$a}<=>$clusters{$run_and_query_and_document}{RANKED}{$b}}
                            keys %{$clusters{$run_and_query_and_document}{RANKED}}) {
      $clusters{$run_and_query_and_document}{SELECTED}{$cluster_id} = 1
        if scalar keys %{$clusters{$run_and_query_and_document}{SELECTED}} < $max_num_of_clusters_per_document;
    }
  }
  
  # Each cluster has a single informative mention so no matter how many response items
  # were present in sparql output, we need to just show one
  my %included;
  $pool->set("HEADER", $header);
  foreach my $response($responses->get("RESPONSES")->toarray()) {
    my $query_id = $response->get("QUERY_ID");
    my $enttype_in_query = $response->get("QUERY")->get("ENTTYPE");
    my $doc_id = $response->get("DOCUMENT_ID");
    next unless $coredocs->exists($doc_id);
    my $cluster_id = $response->get("CLUSTER_ID");
    my $run_id = $response->get("RUN_ID");
    my $run_and_query_and_document = join($concat_key, ($run_id, $query_id, $doc_id));
    # skip this response if the cluster it contains is not one of those
    # selected to be included in the pool
    unless ($clusters{$run_and_query_and_document}{SELECTED}{$cluster_id}) {
      $logger->record_debug_information("SKIPPING_CLUSTER_NOT_SELECTED", $response->get("LINE"), $response->get("WHERE"));
      next;
    }
    # skip if we already included the response for this cluster in the pool
    if ($clusters{$run_and_query_and_document}{INCLUDED}{$cluster_id}) {
      $logger->record_debug_information("SKIPPING_RESPONSE_CLUSTER_INCLUDED", $response->get("LINE"), $response->get("WHERE"));
      next;
    }
    my $fq_mention_span = $response->get("VALUE_PROVENANCE_TRIPLE");
    my (undef, $doceid, $span) = split(":", $fq_mention_span);
    my $mention_span = "$doceid:$span";
    if($fq_mention_span =~ /^(.*?):(.*?)\_/) {
      $doceid = $2;
    }
    my $doce_modality = $self->get("DOCID_MAPPINGS")->get("DOCUMENTELEMENTS")->get("BY_KEY", $doceid)->get("MODALITY");
    my $kit_entry = KitEntry->new($logger);
    $kit_entry->set("HEADER", $header);
    $kit_entry->set("QUERY_ID", $query_id);
    $kit_entry->set("CLASS", $enttype_in_query);
    $kit_entry->set("ID", "<ID>");
    $kit_entry->set("MODALITY", $doce_modality);
    $kit_entry->set("DOCID", $doc_id);
    $kit_entry->set("SPAN", $mention_span);
    $kit_entry->set("CORRECTNESS", "NIL");
    $kit_entry->set("TYPE", "NIL");
    $kit_entry->set("FQEC", "NIL");
    my $uuid = &main::generate_uuid_from_string($kit_entry->tostring());
    my $exists = 0;
    if($previous_pool->exists($query_id)) {
      my $pkit = $previous_pool->get("BY_KEY", $query_id);
      $exists = 1 if $pkit->exists($uuid);
    }
    unless($exists) {
      my $kit = $pool->get("BY_KEY", $query_id);
      $exists = 1 if $kit->exists($uuid);
      $kit->add($kit_entry, $uuid) unless $exists;
      $clusters{$run_and_query_and_document}{INCLUDED}{$cluster_id} = 1;
    }
  }
  $self->set("DELTA_POOL", $pool);
}

sub custom {
  my $a_DOCID = $a->get("DOCID");
  my $a_SPAN = $a->get("SPAN");
  my $b_DOCID = $b->get("DOCID");
  my $b_SPAN = $b->get("SPAN");
  my ($a_DOCEID, $a_SX, $a_SY, $a_EX, $a_EY) = $a_SPAN =~ /^(.*?):\((\d+),(\d+)\)-\((\d+),(\d+)\)$/;
  my ($b_DOCEID, $b_SX, $b_SY, $b_EX, $b_EY) = $b_SPAN =~ /^(.*?):\((\d+),(\d+)\)-\((\d+),(\d+)\)$/;

  ($a_DOCID cmp $b_DOCID ||
  $a_DOCEID cmp $b_DOCEID ||
  $a_SX <=> $b_SX ||
  $a_SY <=> $b_SY ||
  $a_EX <=> $b_EX ||
  $a_EY <=> $b_EY);
}

sub tostring {
  my ($self) = @_;
  my @lines;
  my $pool_header = $self->get("DELTA_POOL")->get("HEADER")->get("LINE");
  push(@lines, $pool_header);
  foreach my $kit_key(sort {$a cmp $b} $self->get("DELTA_POOL")->get("ALL_KEYS")) {
    my $kit = $self->get("DELTA_POOL")->get("BY_KEY", $kit_key);
    foreach my $kit_entry(sort custom $kit->toarray()) {
      push(@lines, $kit_entry->tostring());
    }
  }
  join("\n", @lines);
}

#####################################################################################
# TA2ZeroHopResponsesPool
#####################################################################################

package TA2ZeroHopResponsesPool;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $docid_mappings, $text_document_boundaries, $images_boundingboxes, $keyframes_boundingboxes, $previous_pool, $coredocs, $queries, $queries_to_load, $runs_to_load, $runs_dir, $cas_dir) = @_;
  my $self = {
    __CLASS__ => 'TA2ZeroHopResponsesPool',
    AG_CV_FIELDS => ["?link_cv"],
    CONFIDENCE_AGGREGATION_DIR => $cas_dir,
    COREDOCS => $coredocs,
    DOCID_MAPPINGS => $docid_mappings,
    IMAGE_BOUNDARIES => $images_boundingboxes,
    KEYFRAME_BOUNDARIES => $keyframes_boundingboxes,
    PREVIOUS_POOL => $previous_pool,
    QUERIES => $queries,
    QUERIES_TO_LOAD => $queries_to_load,
    RUNS_TO_LOAD => $runs_to_load,
    RUNS_DIR => $runs_dir,
    TEXT_BOUNDARIES => $text_document_boundaries,
    DELTA_POOL => undef,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load();
  $self;
}

sub load {
  my ($self) = @_;
  my $cas_dir = $self->get("CONFIDENCE_AGGREGATION_DIR");
  my $coredocs = $self->get("COREDOCS");
  my $docid_mappings = $self->get("DOCID_MAPPINGS");
  my $images_boundingboxes = $self->get("IMAGE_BOUNDARIES");
  my $keyframes_boundingboxes = $self->get("KEYFRAME_BOUNDARIES");
  my $queries = $self->get("QUERIES");
  my $queries_to_load = $self->get("QUERIES_TO_LOAD");
  my $queries_task_and_type = $queries->get("TASK_AND_TYPE_CODE");
  my $runs_to_load = $self->get("RUNS_TO_LOAD");
  my $runs_dir = $self->get("RUNS_DIR");
  my $text_document_boundaries = $self->get("TEXT_BOUNDARIES");
  my $logger = $self->get("LOGGER");
  my $responses_pool;

  my $responses = ResponseSet->new($logger,
                      $queries,
                      $docid_mappings,
                      $text_document_boundaries,
                      $images_boundingboxes,
                      $keyframes_boundingboxes,
                      $runs_dir,
                      $runs_to_load,
                      $queries_to_load,
                      $cas_dir);

  $self->generate_pool($responses);
}

sub generate_pool {
  my ($self, $responses) = @_;
  my $logger = $self->get("LOGGER");
  my $coredocs = $self->get("COREDOCS");
  my $pool = Pool->new($logger, "TA2_ZH");
  my $previous_pool = $self->get("PREVIOUS_POOL");
  my $header_line = join("\t", qw(KBID CLASS ID MODALITY DOCID SPAN CORRECTNESS TYPE));
  my $header = Header->new($logger, $header_line);
  my $concat_key = ":";
  
  # select the clusters to be pooled
  my %clusters;
  foreach my $response($responses->get("RESPONSES")->toarray()) {
    my $query_id = $response->get("QUERY_ID");
    my $doc_id = $response->get("DOCUMENT_ID");
    my $cluster_id = $response->get("CLUSTER_ID");
    my $run_id = $response->get("RUN_ID");
    my $cluster_rank = $response->get("CLUSTER_RANK");
    my $run_and_query = join($concat_key, ($run_id, $query_id));
    $clusters{$run_and_query}{RANKED}{$cluster_id} = $cluster_rank;
  }
  foreach my $run_and_query (keys %clusters) {
    my (undef, $query_id) = split($concat_key, $run_and_query);
    my $max_num_of_clusters = $self->get("QUERIES_TO_LOAD")->get("BY_KEY", $query_id)->get("max_num_clusters");
    foreach my $cluster_id(sort {$clusters{$run_and_query}{RANKED}{$a}<=>$clusters{$run_and_query}{RANKED}{$b}}
                            keys %{$clusters{$run_and_query}{RANKED}}) {
      $clusters{$run_and_query}{SELECTED}{$cluster_id} = 1
        if scalar keys %{$clusters{$run_and_query}{SELECTED}} < $max_num_of_clusters;
    }
  }
  # Select the top k informative mentions for selected clusters
  my @selected_responses;
  foreach my $run_and_query (keys %clusters) {
    my ($run_id, $query_id) = split($concat_key, $run_and_query);
    # iterate over selected clusters only
    foreach my $cluster_id(keys %{$clusters{$run_and_query}{SELECTED}}) {
      # selected responses that belong to a soecific run, query and cluster
      my @all_responses = grep {$_->get("RUN_ID") eq $run_id &&
                              $_->get("QUERY_ID") eq $query_id &&
                              $_->get("CLUSTER_ID") eq $cluster_id}
                      $responses->get("RESPONSES")->toarray();
      my %responses_per_document;
      foreach my $response(@all_responses) {
        if(exists $responses_per_document{$response->get("DOCUMENT_ID")}) {
          $logger->record_problem("MULTIPLE_INFORMATIVE_JUSTIFICATIONS_PER_DOCUMENT", $run_and_query, $cluster_id, $response->get("DOCUMENT_ID"), $response->get("WHERE"));
          $responses_per_document{$response->get("DOCUMENT_ID")} = $response
            if($response->get("JUSTIFICATION_CONFIDENCE") > $responses_per_document{$response->get("DOCUMENT_ID")}->get("JUSTIFICATION_CONFIDENCE"));
        }
        else {
          $responses_per_document{$response->get("DOCUMENT_ID")} = $response;
        }
      }
      my @responses = map {$responses_per_document{$_}} keys %responses_per_document;
      my $max_num_informative_mentions = $self->get("QUERIES_TO_LOAD")->get("BY_KEY", $query_id)->get("max_num_informative_mentions");
      my $i = 0;
      foreach my $response(sort {$responses->get("AG_CV", $b, $self->get("AG_CV_FIELDS")) <=> $responses->get("AG_CV", $a, $self->get("AG_CV_FIELDS"))
                                  || $a->get("VALUE_PROVENANCE_TRIPLE") cmp $b->get("VALUE_PROVENANCE_TRIPLE")}
                            @responses) {
        last if $i == $max_num_informative_mentions;
        next unless $coredocs->exists($response->get("DOCUMENT_ID"));
        push(@selected_responses, $response);
        $i++;
      }
    }
  }

  # build pool from selected informative mentions
  my %included;
  $pool->set("HEADER", $header);
  foreach my $response(@selected_responses) {
    my $query_id = $response->get("QUERY_ID");
    my $refkbid_in_query = $response->get("QUERY")->get("REFERENCE_KBID");
    my $doc_id = $response->get("DOCUMENT_ID");
    my $cluster_id = $response->get("CLUSTER_ID");
    my $run_id = $response->get("RUN_ID");
    my $run_and_query = join($concat_key, ($run_id, $query_id));
    # skip this response if the cluster it contains is not one of those
    # selected to be included in the pool
    unless ($clusters{$run_and_query}{SELECTED}{$cluster_id}) {
      $logger->record_debug_information("SKIPPING_CLUSTER_NOT_SELECTED", $response->get("LINE"), $response->get("WHERE"));
      next;
    }
    my $fq_mention_span = $response->get("VALUE_PROVENANCE_TRIPLE");
    my (undef, $doceid, $span) = split(":", $fq_mention_span);
    my $mention_span = "$doceid:$span";
    if($fq_mention_span =~ /^(.*?):(.*?)\_/) {
        $doceid = $2;
    }
    my $doce_modality = $self->get("DOCID_MAPPINGS")->get("DOCUMENTELEMENTS")->get("BY_KEY", $doceid)->get("MODALITY");
    my $kit_entry = KitEntry->new($logger);
    $kit_entry->set("HEADER", $header);
    $kit_entry->set("KBID", $refkbid_in_query);
    $kit_entry->set("CLASS", "NIL");
    $kit_entry->set("ID", "<ID>");
    $kit_entry->set("MODALITY", $doce_modality);
    $kit_entry->set("DOCID", $doc_id);
    $kit_entry->set("SPAN", $mention_span);
    $kit_entry->set("CORRECTNESS", "NIL");
    $kit_entry->set("TYPE", "NIL");
    my $uuid = &main::generate_uuid_from_string($kit_entry->tostring());
    my $exists = 0;
    if($previous_pool->exists($refkbid_in_query)) {
      my $pkit = $previous_pool->get("BY_KEY", $refkbid_in_query);
      $exists = 1 if $pkit->exists($uuid);
    }
    unless($exists) {
      my $kit = $pool->get("BY_KEY", $query_id);
      $exists = 1 if $kit->exists($uuid);
      $kit->add($kit_entry, $uuid) unless $exists;
    }
  }
  $self->set("DELTA_POOL", $pool);
}

sub custom {
  my $a_DOCID = $a->get("DOCID");
  my $a_SPAN = $a->get("SPAN");
  my $b_DOCID = $b->get("DOCID");
  my $b_SPAN = $b->get("SPAN");
  my ($a_DOCEID, $a_SX, $a_SY, $a_EX, $a_EY) = $a_SPAN =~ /^(.*?):\((\d+),(\d+)\)-\((\d+),(\d+)\)$/;
  my ($b_DOCEID, $b_SX, $b_SY, $b_EX, $b_EY) = $b_SPAN =~ /^(.*?):\((\d+),(\d+)\)-\((\d+),(\d+)\)$/;

  ($a_DOCID cmp $b_DOCID ||
  $a_DOCEID cmp $b_DOCEID ||
  $a_SX <=> $b_SX ||
  $a_SY <=> $b_SY ||
  $a_EX <=> $b_EX ||
  $a_EY <=> $b_EY);
}

sub tostring {
  my ($self) = @_;
  my @lines;
  my $pool_header = $self->get("DELTA_POOL")->get("HEADER")->get("LINE");
  push(@lines, $pool_header);
  foreach my $kit_key(sort {$a cmp $b} $self->get("DELTA_POOL")->get("ALL_KEYS")) {
    my $kit = $self->get("DELTA_POOL")->get("BY_KEY", $kit_key);
    foreach my $kit_entry(sort custom $kit->toarray()) {
      push(@lines, $kit_entry->tostring());
    }
  }
  join("\n", @lines);
}

#####################################################################################
# PrevailingTheoryEntry
#####################################################################################

package PrevailingTheoryEntry;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $entry) = @_;
  my $self = {
    __CLASS__ => 'PrevailingTheoryEntry',
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
    __CLASS__ => 'ArgumentSpec',
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
    __CLASS__ => 'EntitySpec',
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
    __CLASS__ => 'EventSpec',
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
    __CLASS__ => 'RelationSpec',
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
  $self->{__CLASS__} = 'PrevailingTheoryContainer';
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
  $self->{__CLASS__} = 'OntologyContainer';
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
    __CLASS__ => 'QueryGenerator',
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
    USED_TA1_CLASS_QUERY_KEYS => Container->new($logger),
    USED_TA1_GRAPH_QUERY_KEYS => Container->new($logger),
    USED_TA2_ZEROHOP_QUERY_KEYS => Container->new($logger),
    USED_TA2_GRAPH_QUERY_KEYS => Container->new($logger),
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
  my $used_query_keys = $self->get("USED_" . $task_short_name . "_GRAPH_QUERY_KEYS");
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
        my $query_key = $edge_label;
        $query_key = $edge_label . "_" . $argument_kbid if $task_long_name eq "task2";
        next if $used_query_keys->exists($query_key);
        my $i = $self->get("NEXT_" . uc($task_long_name) . "_GRAPH_QUERY_NUM");
        $i = $self->normalize_querynum($i);
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
        $used_query_keys->add("KEY", $query_key);
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
  my $used_query_keys = $self->get("USED_TA1_CLASS_QUERY_KEYS");
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
        next if $used_query_keys->exists($query_type);
        # Generate a query at all granularities
        my $i = $self->get("NEXT_TASK1_CLASS_QUERY_NUM");
        $i = $self->normalize_querynum($i);
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
        $used_query_keys->add("KEY", $query_type);
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
  my $used_query_keys = $self->get("USED_TA2_ZEROHOP_QUERY_KEYS");
  foreach my $pt_entry($subcontainer->toarray()) {
    # Is this an entity involved in the prevailing theory?
    my $argument_kbid = $pt_entry->get("ARGUMENT_KBID");
    if($argument_kbid =~ /^\d+$/) {
      # If yes, generate the query
      next if $used_query_keys->exists($argument_kbid);
      my $i = $self->get("NEXT_TASK2_ZEROHOP_QUERY_NUM");
      $i = $self->normalize_querynum($i);
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
      $used_query_keys->add("KEY", $argument_kbid);
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
              PREFIX ldcOnt: <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LDCOntology#>
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

              SELECT DISTINCT
                ?docid      # sourceDocument
                ?query_type # query type
                ?cluster    # ?cluster containing ?member1 of type ?type that matches ?query_type
                ?type       # matching ?type
                ?infj_span  # informativeJustification span
                ?t_cv       # confidenceValue of asserting ?member being of ?type
                ?cm_cv      # confidenceValue of asserting ?member being a member of the ?cluster
                ?j_cv       # confidenceValue of informativeJustification

              WHERE {

                  BIND(ldcOnt:[__TYPE__] AS ?query_type)

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

                  BIND( cfn:getSpan(str(?docid), str(?doceid), str(?_sid), str(?_kfid), str(?_so), str(?_eo), str(?_ulx), str(?_uly), str(?_lrx), str(?_lry), str(?_st), str(?_et) ) AS ?infj_span ) .
              }
  ]]>
END_SPARQL_QUERY
  $sparql;
}

sub get_TA1_GRAPH_SPARQL_QUERY_TEMPLATE {
  my ($self) = @_;
  my $sparql = <<'END_SPARQL_QUERY';
  <![CDATA[
              PREFIX ldcOnt: <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LDCOntology#>
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
              
              SELECT DISTINCT 
                     ?docid        # sourceDocument
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
              
                  BIND (ldcOnt:[__PREDICATE__] AS ?edge_type_q)
              
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
              
                  BIND( cfn:getSpan(str(?docid), str(?oinf_j_doceid), str(?_osid), str(?_okfid), str(?_oso), str(?_oeo), str(?_oulx), str(?_ouly), str(?_olrx), str(?_olry), str(?_ost), str(?_oet) ) AS ?oinf_j_span ) .
              
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
              
                  BIND( cfn:getSpan(str(?docid), str(?sinf_j_doceid), str(?_ssid), str(?_skfid), str(?_sso), str(?_seo), str(?_sulx), str(?_suly), str(?_slrx), str(?_slry), str(?_sst), str(?_set) ) AS ?sinf_j_span ) .
              
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
              
                  BIND( cfn:getSpan(str(?docid), str(?edgecj1_doceid), str(?_ej1sid), str(?_ej1kfid), str(?_ej1so), str(?_ej1eo), str(?_ej1ulx), str(?_ej1uly), str(?_ej1lrx), str(?_ej1lry), str(?_ej1st), str(?_ej1et) ) AS ?ej1_span ) .
              
              
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
              
                  BIND( cfn:getSpan(str(?docid), str(?edgecj2_doceid), str(?_ej2sid), str(?_ej2kfid), str(?_ej2so), str(?_ej2eo), str(?_ej2ulx), str(?_ej2uly), str(?_ej2lrx), str(?_ej2lry), str(?_ej2st), str(?_ej2et) ) AS ?ej2_span ) .
                  BIND(IF(?edge_num_cjs = 1, "", ?ej2_span) AS ?ej2_span)
                  FILTER(?ej1_span > ?ej2_span)
                  BIND(IF(?edge_num_cjs = 1, ?ej1_span, CONCAT(CONCAT(?ej2_span,","),?ej1_span)) AS ?ej_span)
              }
  ]]>
END_SPARQL_QUERY
  $sparql;
}

sub get_TA2_ZEROHOP_SPARQL_QUERY_TEMPLATE {
  my ($self) = @_;
  my $sparql = <<'END_SPARQL_QUERY';
  <![CDATA[
              PREFIX ldcOnt: <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LDCOntology#>
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
              
              
              SELECT DISTINCT
                     ?docid             # sourceDocument
                     ?query_link_target # link target as part of the query
                     ?link_target       # link target in the KB matching ?query_link_target
                     ?cluster           # the ?cluster linked to ?link_target
                     ?infj_span         # informativeJustification span taken from the ?cluster
                     ?j_cv              # confidenceValue of informativeJustification
                     ?link_target       # query reference KB node linked to a ?cluster
                     ?link_cv           # confidenceValue of asserting that ?cluster is the same as reference KB node ?link_target
              
              WHERE {
                  BIND ("[__KBID__]" AS ?query_link_target)
              
                  # Find ?cluster linked to "[__KBID__]"
                  # Find the ?link_cv: confidenceValue of linking to external KB entity
                  ?cluster              a                             aida:SameAsCluster .
                  ?cluster              aida:informativeJustification ?inf_justification .
                  ?cluster              aida:link                     ?ref_kb_link .
                  ?ref_kb_link          a                             aida:LinkAssertion .
                  ?ref_kb_link          aida:linkTarget               ?link_target .
                  ?ref_kb_link          aida:confidence               ?link_confidence .
                  ?link_confidence      aida:confidenceValue          ?link_cv .
                  
                  FILTER(cfn:memberOf(str(?link_target), str(?query_link_target))) .
              
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
              
                  BIND( cfn:getSpan(str(?docid), str(?doceid), str(?_sid), str(?_kfid), str(?_so), str(?_eo), str(?_ulx), str(?_uly), str(?_lrx), str(?_lry), str(?_st), str(?_et) ) AS ?infj_span ) .
              }
  ]]>
END_SPARQL_QUERY
  $sparql;
}

sub get_TA2_GRAPH_SPARQL_QUERY_TEMPLATE {
  my ($self) = @_;
  my $sparql = <<'END_SPARQL_QUERY';
  <![CDATA[
              PREFIX ldcOnt: <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LDCOntology#>
              PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
              PREFIX aida:  <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/InterchangeOntology#>
              PREFIX cfn:   <https://verdi.nextcentury.com/custom-function/>
              PREFIX xsd:   <http://www.w3.org/2001/XMLSchema#>
              
              # Query: [__QUERY_ID__]
              # Query description: Find all edges of type ldcOnt:[__PREDICATE__] such that the object
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
              
              SELECT DISTINCT
                     ?docid           # sourceDocument
                     ?edge_type_q     # edge type in the query
                     ?edge_type       # edge type in response matching the edge type in query
                     ?olink_target_q  # reference KB node given in query
                     ?olink_target    # reference KB node linked to the object of the edge matching ?olink_target_q
                     ?object_cluster  ?objectmo  ?oinf_j_span # object cluster, cluster member and its informativeJustification
                     ?subject_cluster ?subjectmo  # subject cluster, cluster member (its informativeJustification is not needed by LDC for assessment)
                     ?ej_span         # CompoundJustification span(s) for argument assertion
                     ?orfkblink_cv    # confidence of linking the object to the query reference KB ID
                     ?oinf_j_cv       # confidence of object informativeJustification
                     ?obcm_cv         # cluster membership confidence of the object
                     ?edge_cv         # confidence of a compound justification for the argument assertion
                     ?sbcm_cv         # cluster membership confidence of the subject
              
              WHERE {
              
                  BIND ("[__KBID__]" AS ?olink_target_q)
                  BIND (ldcOnt:[__PREDICATE__] AS ?edge_type_q)
              
                  # Find ?objectmo linked to "[__KBID__]"
                  ?objectmo             a                             aida:Entity .
                  ?objectmo             aida:link                     ?objectmo_rfkbl .
              
                  ?objectmo_rfkbl       a                             aida:LinkAssertion .
                  ?objectmo_rfkbl       aida:linkTarget               ?olink_target .
                  ?objectmo_rfkbl       aida:confidence               ?orfkblink_confidence .
                  ?orfkblink_confidence aida:confidenceValue          ?orfkblink_cv .
                  
                  FILTER(cfn:memberOf(str(?olink_target), str(?olink_target_q))) .
              
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
              
                  BIND( cfn:getSpan(str(?docid), str(?oinf_j_doceid), str(?_osid), str(?_okfid), str(?_oso), str(?_oeo), str(?_oulx), str(?_ouly), str(?_olrx), str(?_olry), str(?_ost), str(?_oet) ) AS ?oinf_j_span ) .
              
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
              
                  BIND( cfn:getSpan(str(?docid), str(?sinf_j_doceid), str(?_ssid), str(?_skfid), str(?_sso), str(?_seo), str(?_sulx), str(?_suly), str(?_slrx), str(?_slry), str(?_sst), str(?_set) ) AS ?sinf_j_span ) .
              
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
              
                  BIND( cfn:getSpan(str(?docid), str(?edgecj1_doceid), str(?_ej1sid), str(?_ej1kfid), str(?_ej1so), str(?_ej1eo), str(?_ej1ulx), str(?_ej1uly), str(?_ej1lrx), str(?_ej1lry), str(?_ej1st), str(?_ej1et) ) AS ?ej1_span ) .
              
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
              
                  BIND( cfn:getSpan(str(?docid), str(?edgecj2_doceid), str(?_ej2sid), str(?_ej2kfid), str(?_ej2so), str(?_ej2eo), str(?_ej2ulx), str(?_ej2uly), str(?_ej2lrx), str(?_ej2lry), str(?_ej2st), str(?_ej2et) ) AS ?ej2_span ) .
                  BIND(IF(?edge_num_cjs = 1, "", ?ej2_span) AS ?ej2_span)
                  FILTER(?ej1_span > ?ej2_span)
                  BIND(IF(?edge_num_cjs = 1, ?ej1_span, CONCAT(CONCAT(?ej2_span,","),?ej1_span)) AS ?ej_span)
              }
  ]]>
END_SPARQL_QUERY
  $sparql;
}

sub normalize_querynum {
  my ($self, $querynum) = @_;
  my $normalized_querynum = $querynum;
  while($querynum < 1000) {
    $normalized_querynum = "0" . $normalized_querynum;
    $querynum *= 10;
  }
  $normalized_querynum;
}

#####################################################################################
# QuerySet
#####################################################################################

package QuerySet;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $dtd_filename, $xml_filename) = @_;
  my $self = {
    __CLASS__ => 'QuerySet',
    DTD_FILENAME => $dtd_filename,
    XML_FILENAME => $xml_filename,
    QUERIES => Container->new($logger, "Query"),
    QUERYTYPE => undef,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load() if -e $xml_filename;
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
  my $output_filename = $self->get("XML_FILENAME");
  $self->get("LOGGER")->NIST_die("Output file exists") if -e $output_filename;
  open(my $program_output_xml, ">:utf8", $output_filename)
    or $self->get("LOGGER")->record_problem('MISSING_FILE', $output_filename, $!);
  print $program_output_xml "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
  print $program_output_xml "<$query_type>\n";
  print $program_output_xml $self->tostring(2);
  print $program_output_xml "<\/$query_type>\n";
  close($program_output_xml);
}

sub get_MATCHING_QUERIES {
  my ($self, %criteria) = @_;
  my @candidate_queries = grep {$_->get("PREDICATE") eq $criteria{PREDICATE}} $self->get("QUERIES")->toarray();
  if($criteria{OBJECT}) {
    my @criteria_objects = split(/\|/, $criteria{OBJECT});
    my %matched_queries;
    foreach my $query(@candidate_queries) {
      my %query_objects = map {$_=>1} split(/\|/, $query->get("OBJECT"));
      foreach my $criteria_object(@criteria_objects) {
        $matched_queries{$query->get("QUERYID")} = $query if $query_objects{$criteria_object};
      }
    }
    return values %matched_queries;
  }
  else {
    return @candidate_queries;
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

sub get_TASK_AND_TYPE_CODE {
  my ($self) = @_;
  my $code;
  foreach my $query($self->get("QUERIES")->toarray()) {
    my $queryid = $query->get("QUERYID");
    my ($code_) = $queryid =~ /^AIDA_(TA\S_\S\S)_/;
    $code = $code_ unless $code;
    $self->get("LOGGER")->record_problem("MULTIPLE_TASK_AND_TYPE_IN_QUERIES", $code, $code_, $query->get("XML_OBJECT")->get("WHERE"))
      if $code ne $code_;
  }
  $code;
}

sub exists {
  my ($self, $query_id) = @_;
  $self->get("QUERIES")->exists($query_id);
}

sub toarray {
  my ($self) = @_;
  $self->get("QUERIES")->toarray();
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
    __CLASS__ => 'ClassQuery',
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
    __CLASS__ => 'ZeroHopQuery',
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
    __CLASS__ => 'GraphQuery',
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
  $self->set("OBJECT", $self->get("XML_OBJECT")->get("CHILD", "object")->get("ELEMENT"));
  $self->set("SPARQL", $self->get("XML_OBJECT")->get("CHILD", "sparql")->get("ELEMENT"));
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
    __CLASS__ => 'Edge',
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
    __CLASS__ => 'Justification',
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
    __CLASS__ => 'StringDescriptor',
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
    __CLASS__ => 'NonStringDescriptor',
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
    __CLASS__ => "DocumentIDsMappings",
    FILENAME => $filename,
    DOCUMENTS => Documents->new($logger),
    DOCUMENTELEMENTS => DocumentElements->new($logger),
    ENCODINGFORMAT_TO_MODALITY_MAPPINGS => EncodingFormatToModalityMappings->new($logger),
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
      my $modality = $self->get("ENCODINGFORMAT_TO_MODALITY_MAPPINGS")->get("MODALITY_FROM_ENCODING_FORMAT", $detype);
      my $is_core = 0;
      $is_core = 1 if $self->get("COREDOCS")->exists($document_id);
      my $document = $self->get("DOCUMENTS")->get("BY_KEY", $document_id);
      $document->set("DOCUMENTID", $document_id);
      $document->set("IS_CORE", $is_core);
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
  $self->{__CLASS__} = 'Documents';
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
  $self->{__CLASS__} = 'DocumentElements';
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
    __CLASS__ => 'Document',
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
    __CLASS__ => 'DocumentElement',
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
    __CLASS__ => 'CoreDocs',
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
# Assessments
#####################################################################################

package Assessments;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $assessments_dir, $query_type) = @_;
  my $self = {
    __CLASS__ => 'QREL',
    ASSESSMENTS_DIR => $assessments_dir,
    QUERY_TYPE => $query_type,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load();
  $self;
}

sub normalize {
  my ($key, $value) = @_;
  my %normalize = (correct => "CORRECT", wrong => "INCORRECT", yes => "YES", no => "NO");
  my %keys_to_normalize = map {$_=>1} qw(ASSESSMENT OBJECT_LINKABILITY PREDICATE_JUSTIFICATION_CORRECTNESS);
  $value = $normalize{$value} if $keys_to_normalize{$key} && $normalize{$value};
  $value;
}

sub load {
  my ($self) = @_;
  my $query_type = $self->get("QUERY_TYPE");
  $query_type =~ s/_query$//;
  my $method = $self->can("load_$query_type");
  return $method->($self) if $method;
  $self->get("LOGGER")->NIST_die("No matching load function for $query_type");
}

sub load_class {
  my ($self) = @_;
  my %normalize = (correct => "CORRECT", wrong => "INCORRECT");
  my $assessments_dir = $self->get("ASSESSMENTS_DIR");
  my $query_type = $self->get("QUERY_TYPE");
  my $query_type_specifice_assessments_dir = $assessments_dir . "/data/class";
  my $header_line = join("\t", qw(QUERYID CLASS ID MODALITY DOCID MENTION_SPAN ASSESSMENT TYPE FQEC));
  my $header = Header->new($self->get("LOGGER"), $header_line);
  my $next_generated_fqec_num = 1001;
  my %generated_fqecs;
  foreach my $filename(<$query_type_specifice_assessments_dir/*/*.tab>) {
    my $filehandler = FileHandler->new($self->get("LOGGER"), $filename, $header);
    my $entries = $filehandler->get("ENTRIES");
    foreach my $entry($entries->toarray()) {
      my ($queryid, $docid, $mention_span, $assessment, $fqec_read, $where)
        = map {$entry->get($_)} qw(QUERYID DOCID MENTION_SPAN ASSESSMENT FQEC WHERE);
      my $query_and_document = "$queryid:$docid";
      my $key = "$queryid:$docid:$mention_span";
      if($self->exists($key)) {
        my $existing_assessment = $self->get("BY_KEY", $key)->{"ASSESSMENT"};
        my $existing_linenum = $self->get("BY_KEY", $key)->{WHERE}{LINENUM};
        if($existing_assessment ne $assessment) {
          my $filename = $where->{FILENAME};
          $self->{LOGGER}->record_problem("MULTIPLE_INCOMPATIBLE_ZH_ASSESSMENTS",
                            $queryid,
                            $mention_span,
                            {FILENAME => $filename, LINENUM => "$existing_linenum, $where->{LINENUM}"});
        }
      }
      my $fqec = $fqec_read;
      if($normalize{$assessment} eq "CORRECT" && ($fqec eq "NIL" || $fqec eq "" || !$fqec) ) {
        # the entity is singleton therefore it needs a generated FQEC
        unless($generated_fqecs{$query_and_document}{$mention_span}) {
          $fqec = "NILG$next_generated_fqec_num";
          $next_generated_fqec_num++;
          $generated_fqecs{$query_and_document}{$mention_span} = $fqec;
        }
        $fqec = $generated_fqecs{$query_and_document}{$mention_span};
      }
      my $assessment_entry = SuperObject->new($self->get("LOGGER"));
      $assessment_entry->set("ASSESSMENT", $normalize{$assessment});
      $assessment_entry->set("DOCUMENT_ID", $docid);
      $assessment_entry->set("QUERYID", $queryid);
      $assessment_entry->set("MENTION_SPAN", $mention_span);
      $assessment_entry->set("FQEC", $fqec);
      $assessment_entry->set("WHERE", $where);
      $self->add($assessment_entry, $key) unless $self->exists($key);
      my $line = "QUERYID=$queryid " .
                 "DOCUMENT_ID=$docid " .
                 "MENTION=$mention_span " .
                 "ASSESSMENT=$normalize{$assessment} " .
                 "FQEC_READ=$fqec_read " .
                 "FQEC=$fqec ";
      $self->get("LOGGER")->record_debug_information("GROUND_TRUTH", $line, $assessment_entry->get("WHERE"));
    }
    $filehandler->cleanup();
  }
}

sub load_zerohop {
  my ($self) = @_;
  my %normalize = (correct => "CORRECT", wrong => "INCORRECT");
  my $assessments_dir = $self->get("ASSESSMENTS_DIR");
  my $query_type = $self->get("QUERY_TYPE");
  my $query_type_specifice_assessments_dir = $assessments_dir . "/data/zero-hop";
  my $header_line = join("\t", qw(NODEID CLASS ID MODALITY DOCUMENT_ID MENTION_SPAN ASSESSMENT TYPE));
  my $header = Header->new($self->get("LOGGER"), $header_line);
  foreach my $filename(<$query_type_specifice_assessments_dir/*/*.tab>) {
    my $filehandler = FileHandler->new($self->get("LOGGER"), $filename, $header);
    my $entries = $filehandler->get("ENTRIES");
    foreach my $entry($entries->toarray()) {
      my ($nodeid, $docid, $mention_span, $assessment, $where)
        = map {$entry->get($_)} qw(NODEID DOCUMENT_ID MENTION_SPAN ASSESSMENT WHERE);
      my $key = "$nodeid:$docid:$mention_span";
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
      my $assessment_entry = SuperObject->new($self->get("LOGGER"));
      map {$assessment_entry->set($_, &normalize($_, $entry->get($_)))}
        qw(ASSESSMENT
           DOCUMENT_ID
           REFERENCE_KBID
           MENTION_SPAN
           LINE
           WHERE);
      $self->add($assessment_entry, $key) unless $self->exists($key);
    }
    $filehandler->cleanup();
  }
}

sub load_graph {
  my ($self) = @_;
  my %normalize = (correct => "CORRECT", wrong => "INCORRECT");
  my $assessments_dir = $self->get("ASSESSMENTS_DIR");
  my $query_type_specifice_assessments_dir = $assessments_dir . "/data/graph";
  my $header_line = join("\t", qw(KIT_ID RESPONSE_ID PREDICATE DOCUMENT_ID SUBJECT_TYPE SUBJECT_JUSTIFICATION OBJECT_TYPE OBJECT_JUSTIFICATION PREDICATE_JUSTIFICATION PREDICATE_JUSTIFICATION_CORRECTNESS OBJECT_LINKABILITY OBJECT_FQEC SUBJECT_FQEC));
  my $header = Header->new($self->get("LOGGER"), $header_line);
  my $next_generated_fqec_num = 1001;
  foreach my $filename(<$query_type_specifice_assessments_dir/*/*.tab>) {
    my $filehandler = FileHandler->new($self->get("LOGGER"), $filename, $header);
    my $entries = $filehandler->get("ENTRIES");
    foreach my $entry($entries->toarray()) {
      my ($edge_label, $docid, $predicate_justification, $object_justification, $where)
        = map {$entry->get($_)} qw(PREDICATE DOCUMENT_ID PREDICATE_JUSTIFICATION OBJECT_JUSTIFICATION WHERE);
      my $key = "$edge_label:$docid:$predicate_justification:$object_justification";
      if($self->exists($key)) {
        my ($efilename, $elinenum) = map {$self->get("BY_KEY", $key)->{WHERE}{$_}} qw(FILENAME LINENUM);
        my ($filename, $linenum) = map {$where->{$_}} qw(FILENAME LINENUM);
        $self->{LOGGER}->record_problem("MULTIPLE_GRAPH_ASSESSMENTS",
                          $key,
                          $filename, $linenum, $efilename, $elinenum,
                          "NO_SOURCE");
      }
      my $assessment_entry = SuperObject->new($self->get("LOGGER"));
      map {$assessment_entry->set($_, &normalize($_, $entry->get($_)))}
        qw(PREDICATE
           DOCUMENT_ID
           OBJECT_JUSTIFICATION
           PREDICATE_JUSTIFICATION_CORRECTNESS
           PREDICATE_JUSTIFICATION
           OBJECT_LINKABILITY
           OBJECT_FQEC
           SUBJECT_FQEC
           LINE
           WHERE);
      $assessment_entry->set("SUBJECT_FQEC_READ", $assessment_entry->get("SUBJECT_FQEC"));
      $assessment_entry->set("OBJECT_FQEC_READ", $assessment_entry->get("OBJECT_FQEC"));
      if($assessment_entry->get("PREDICATE_JUSTIFICATION_CORRECTNESS") eq "CORRECT" &&
          $assessment_entry->get("OBJECT_LINKABILITY") eq "YES") {
        if($assessment_entry->get("SUBJECT_FQEC") eq "NIL" || $assessment_entry->get("SUBJECT_FQEC") eq "" || !$assessment_entry->get("SUBJECT_FQEC")) {
          my $generated_fqec = "NILG$next_generated_fqec_num";
          $assessment_entry->set("SUBJECT_FQEC", $generated_fqec);
          $next_generated_fqec_num++;
        }
        if($assessment_entry->get("OBJECT_FQEC") eq "NIL" || $assessment_entry->get("OBJECT_FQEC") eq "" || !$assessment_entry->get("OBJECT_FQEC")) {
          my $generated_fqec = "NILG$next_generated_fqec_num";
          $assessment_entry->set("OBJECT_FQEC", $generated_fqec);
          $next_generated_fqec_num++;
        }
      }
      $self->add($assessment_entry, $key) unless $self->exists($key);
      my $line = "RAW " . join(" ",
                      map {$_ . "=" . $assessment_entry->get($_)}
                        qw(PREDICATE
                           DOCUMENT_ID
                           PREDICATE_JUSTIFICATION
                           OBJECT_JUSTIFICATION
                           PREDICATE_JUSTIFICATION_CORRECTNESS
                           OBJECT_LINKABILITY
                           OBJECT_FQEC_READ
                           OBJECT_FQEC
                           SUBJECT_FQEC_READ
                           SUBJECT_FQEC));
      $self->get("LOGGER")->record_debug_information("GROUND_TRUTH", $line, $assessment_entry->get("WHERE"));
    }
    $filehandler->cleanup();
  }
}

#####################################################################################
# Frames
#####################################################################################

package Frames;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $queries_to_score, $code) = @_;
  my $self = $class->SUPER::new($logger, 'Frame');
  $self->{__CLASS__} = 'Frames';
  $self->{QUERIES_TO_SCORE} = $queries_to_score;
  $self->{FRAMEIDS_BY_QUERYID} = ();
  $self->{QUERYIDS_BY_FRAMEID} = ();
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self->load() if $code eq "TA2_GR";
  $self;
}

sub get_FRAMEIDS_FOR_QUERY {
  my ($self, $query_id) = @_;
  keys %{$self->{FRAMEIDS_BY_QUERYID}{$query_id}};
}

sub get_QUERYIDS_FOR_FRAME {
  my ($self, $frame_id) = @_;
  keys %{$self->{QUERYIDS_BY_FRAMEID}{$frame_id}};
}

sub load {
  my ($self) = @_;
  foreach my $entry($self->get("QUERIES_TO_SCORE")->toarray()){
    foreach my $frame_id(split(",", $entry->get("frame_ids"))) {
      $self->{FRAMEIDS_BY_QUERYID}{$entry->get("query_id")}{$frame_id} = 1;
      $self->{QUERYIDS_BY_FRAMEID}{$frame_id}{$entry->get("query_id")} = 1;
      $self->get("BY_KEY", $frame_id)->add("KEY", $entry->get("query_id"));
    }
  }
}

#####################################################################################
# Frame
#####################################################################################

package Frame;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $filename) = @_;
  my $self = $class->SUPER::new($logger, 'SuperObject');
  $self->{__CLASS__} = 'Frame';
  $self->{FILENAME} = $filename;
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

#####################################################################################
# SalientEdges
#####################################################################################

package SalientEdges;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $filename) = @_;
  my $self = {
    __CLASS__ => 'SalientEdges',
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
    my $subject = $entry->get("subject");
    my $role = $entry->get("role");
    $self->get("LOGGER")->record_debug_information("SALIENT_READ", "LINE " . $entry->get("LINE"), $entry->get("WHERE"));
    foreach my $object(split/\|/, $entry->get("object")) {
      $self->add($entry, "$subject:$role:LDC2019E43:$object");
      $self->get("LOGGER")->record_debug_information("SALIENT_READ", "RECORDED SUBJECT=$subject ROLE=$role OBJECT=LDC2019E43:$object", $entry->get("WHERE"));
    }
  }
  $filehandler->cleanup();
}

#####################################################################################
# ScoresManager
#####################################################################################

package ScoresManager;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $runid, $docid_mappings, $queries, $salient_edges, $responses, $assessments, $queries_to_score, $strategy) = @_;
  my $self = {
    __CLASS__ => 'ScoresManager',
    DOCID_MAPPINGS => $docid_mappings,
    QUERIES => $queries,
    SALIENT_EDGES => $salient_edges,
    RESPONSES => $responses,
    ASSESSMENTS => $assessments,
    QUERY_TYPE => $queries->get("QUERYTYPE"),
    QUERIES_TO_SCORE => $queries_to_score,
    RUNID => $runid,
    STRATEGY => $strategy,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->score_responses();
  $self;
}

sub score_responses {
  my ($self) = @_;
  my ($docid_mappings, $responses, $assessments, $query_type, $queries_to_score, $queries, $salient_edges, $runid, $strategy, $logger)
    = map {$self->get($_)} qw(DOCID_MAPPINGS RESPONSES ASSESSMENTS QUERY_TYPE QUERIES_TO_SCORE QUERIES SALIENT_EDGES RUNID STRATEGY LOGGER);
  my $scores;
  $scores = ClassScores->new($logger, $runid, $docid_mappings, $queries, $responses, $assessments, $queries_to_score) if($query_type eq "class_query");
  $scores = ZeroHopScores->new($logger, $runid, $docid_mappings, $queries, $responses, $assessments, $queries_to_score) if($query_type eq "zerohop_query");
  $scores = GraphScores->new($logger, $runid, $docid_mappings, $queries, $salient_edges, $responses, $assessments, $queries_to_score, $strategy) if($query_type eq "graph_query");
  $self->set("SCORES", $scores);
}

sub print_lines {
  my ($self, $program_output) = @_;
  $self->get("SCORES")->print_lines($program_output);
}

#####################################################################################
# ClassScores
#####################################################################################

package ClassScores;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $runid, $docid_mappings, $queries, $responses, $assessments, $queries_to_score) = @_;
  my $self = {
    __CLASS__ => 'ClassScores',
    AG_CV_FIELDS => [qw(?t_cv ?j_cv ?cm_cv)],
    AP_RANKING_SCORE_FIELDS => [qw(?t_cv ?j_cv ?cm_cv)],
    ASSESSMENTS => $assessments,
    DOCID_MAPPINGS => $docid_mappings,
    QUERIES => $queries,
    QUERIES_TO_SCORE => $queries_to_score,
    RESPONSES => $responses,
    RUNID => $runid,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->score_responses();
  $self;
}

sub get_AP_RANKING_SCORE {
  my ($self, $response) = @_;
  $self->get("RESPONSES")->get("AG_CV", $response, $self->get("AP_RANKING_SCORE_FIELDS"));
}

sub get_AP {
  my ($self, $tie_breaking_criteria, $num_ground_truth, $max_num_ground_truth, @responses) = @_;
  return 0 unless $num_ground_truth;
  my %ranked_responses;
  my $rank = 1;
  my $correct_at_rank = 0;
  my $sum_precision = 0;
  if($tie_breaking_criteria eq "BESTCASE") {
    @responses = sort {$self->get("AP_RANKING_SCORE", $b) <=> $self->get("AP_RANKING_SCORE", $a) ||
                              $b->get("CORRECTNESS_CODE") <=> $a->get("CORRECTNESS_CODE")} @responses;
  }
  elsif($tie_breaking_criteria eq "WORSTCASE") {
    @responses = sort {$self->get("AP_RANKING_SCORE", $b) <=> $self->get("AP_RANKING_SCORE", $a) ||
                              $a->get("CORRECTNESS_CODE") <=> $b->get("CORRECTNESS_CODE")} @responses;
  }
  elsif($tie_breaking_criteria eq "TRECEVAL") {
    @responses = sort {$self->get("AP_RANKING_SCORE", $b) <=> $self->get("AP_RANKING_SCORE", $a) ||
                              $b->get("VALUE_PROVENANCE_TRIPLE") cmp $a->get("VALUE_PROVENANCE_TRIPLE") ||
                              $b->get("CLUSTER_ID") cmp $a->get("CLUSTER_ID") } @responses;
  }
  else {
    $self->get("LOGGER")->NIST_die("Unknown tie breaking criteria: $tie_breaking_criteria");
  }
  foreach my $response(@responses) {
    my $correctness = $response->get("CORRECTNESS");
    next if $correctness eq "IGNORE";
    $ranked_responses{$rank} = $response;
    my $fqec = $response->get("ASSESSMENT_ENTRY")->get("FQEC") || "N/A";
    if($correctness eq "RIGHT" && $rank < $max_num_ground_truth) {
      $correct_at_rank++;
      $sum_precision += $correct_at_rank/$rank;
    }
    my ($query_id, $docid, $mention_span, $cluster_id, $run_id)
      = map {$response->get($_)} qw(QUERY_ID DOCUMENT_ID VALUE_PROVENANCE_TRIPLE CLUSTER_ID RUN_ID);
    my $score = $self->get("AP_RANKING_SCORE", $response);
    my $line = "$tie_breaking_criteria $query_id $docid $mention_span $rank $score $run_id $correctness $fqec $cluster_id";
    $self->get("LOGGER")->record_debug_information("AP_SUBMISSION_LINE", $line, $response->get("WHERE"));
    $rank++;
  }

  my $ap = $sum_precision / (($num_ground_truth <= $max_num_ground_truth) ? $num_ground_truth : $max_num_ground_truth);
  $self->get("LOGGER")->NIST_die("AP > 1") if $ap > 1;
  $ap;
}

sub score_responses {
  my ($self) = @_;
  my ($logger, $runid, $docid_mappings, $queries, $responses, $assessments, $queries_to_score)
    = map {$self->get($_)} qw(LOGGER RUNID DOCID_MAPPINGS QUERIES RESPONSES ASSESSMENTS QUERIES_TO_SCORE);
  my $scores = ClassScoresPrinter->new($logger);
  my %ground_truth;
  foreach my $assessment_entry($assessments->toarray()) {
    my ($query_id, $docid, $mention_span, $assessment, $fqec) =
      map {$assessment_entry->get($_)} qw(QUERYID DOCUMENT_ID MENTION_SPAN ASSESSMENT FQEC);
    $mention_span = "$docid:$mention_span";
    my $query_and_document = "$query_id:$docid";
    if($assessment eq "CORRECT") {
      $ground_truth{$query_and_document}{MENTION_TO_FQECS}{$mention_span}{$fqec} = 1;
      $ground_truth{$query_and_document}{FQEC_TO_MENTIONS}{$fqec}{$mention_span} = 1;
    }
  }

  my %candidate_responses;
  foreach my $response($responses->get("RESPONSES")->toarray()) {
    my ($query_id, $cluster_id, $cluster_rank, $docid, $mention_span)
      = map {$response->get($_)} qw(QUERY_ID CLUSTER_ID CLUSTER_RANK DOCUMENT_ID VALUE_PROVENANCE_TRIPLE);
    next unless $queries_to_score->exists($query_id);
    my $query_and_document = "$query_id:$docid";
    my $max_cluster_rank = $queries_to_score->get("BY_KEY", $query_id)->get("max_num_clusters");
    # all the responses get considered as SUBMITTED-A
    $response->set("SUBMITTED-A", 1);
    # response that are at rank higher than max_cluster_rank are tagged as SUBMITTED-B
    $response->set("SUBMITTED-B", 1) if $cluster_rank <= $max_cluster_rank;
    # responses from coredocs get tagged as SUBMITTED-C
    $response->set("SUBMITTED-C", 1) if $docid_mappings->get("COREDOCS")->exists($docid);
    # responses from coredocs are candidate responses
    if($docid_mappings->get("COREDOCS")->exists($docid)) {
      my $informative_justification = $response->get("VALUE_PROVENANCE_TRIPLE");
      push(@{$candidate_responses{$query_and_document}{$cluster_id}{$informative_justification}}, $response);
    }
    # otherwise, the response is not considered
    else {
      $response->set("NOT-CONSIDERED", 1);
    }
  }

  my %selected_responses;
  foreach my $query_and_document(keys %candidate_responses) {
    foreach my $cluster_id(keys %{$candidate_responses{$query_and_document}}) {
      my ($informative_justification, $error) = keys %{$candidate_responses{$query_and_document}{$cluster_id}};
      # SANITY CHECK: Were multiple informative justifications provided for a this run-query-document-cluster?
      $logger->NIST_die("Multiple informative justifications provided for $runid:$query_and_document:$cluster_id")
        if $error;
      # The response with the highest AG_CV is selected as submitted; other responses are not considered
      my ($response, @other_responses) = sort {$responses->get("AG_CV", $b, $self->get("AG_CV_FIELDS")) <=> $responses->get("AG_CV", $a, $self->get("AG_CV_FIELDS"))
                                  || $a->get("VALUE_PROVENANCE_TRIPLE") cmp $b->get("VALUE_PROVENANCE_TRIPLE")}
                           @{$candidate_responses{$query_and_document}{$cluster_id}{$informative_justification}};

      map {$_->set("NOT-CONSIDERED", 1)} @other_responses;
      $response->set("SUBMITTED", 1);
      if ($response->get("SUBMITTED-B")) {
        $response->set("POOLED", 1);
      }
      else {
        $response->set("NOT-CONSIDERED", 1)
      }
      push(@{$selected_responses{$query_and_document}}, $response) if $response->get("POOLED");
    }
  }

  my %categorized_submissions;
  my %correct_found;
  foreach my $response(sort {$responses->get("AG_CV", $b, $self->get("AG_CV_FIELDS")) <=> $responses->get("AG_CV", $a, $self->get("AG_CV_FIELDS"))
                                  || $a->get("VALUE_PROVENANCE_TRIPLE") cmp $b->get("VALUE_PROVENANCE_TRIPLE")}
                          $responses->get("RESPONSES")->toarray()) {
    my ($query_id, $docid, $mention_span, $cluster_id)
      = map {$response->get($_)} qw(QUERY_ID DOCUMENT_ID VALUE_PROVENANCE_TRIPLE CLUSTER_ID);
    my $query_and_document = "$query_id:$docid";
    # don't collect any more stats unless there is ground truth for this query-document
    next unless $ground_truth{$query_and_document}{FQEC_TO_MENTIONS};
    my $fqec = "N/A";
    if($response->get("NOT-CONSIDERED")) {
      push(@{$categorized_submissions{$query_and_document}{"NOT-CONSIDERED"}}, $response);
      $response->{ASSESSMENT}{"PRE-POLICY"}{"NOT-CONSIDERED"} = 1;
      $response->{ASSESSMENT}{"POST-POLICY"}{"NOT-CONSIDERED"} = 1;
    }
    if($response->get("SUBMITTED-A")) {
      push(@{$categorized_submissions{$query_and_document}{"SUBMITTED-A"}}, $response);
      $response->{ASSESSMENT}{"PRE-POLICY"}{"SUBMITTED-A"} = 1;
    }
    if($response->get("SUBMITTED-B")) {
      push(@{$categorized_submissions{$query_and_document}{"SUBMITTED-B"}}, $response);
      $response->{ASSESSMENT}{"PRE-POLICY"}{"SUBMITTED-B"} = 1;
    }
    if($response->get("SUBMITTED-C")) {
      push(@{$categorized_submissions{$query_and_document}{"SUBMITTED-C"}}, $response);
      $response->{ASSESSMENT}{"PRE-POLICY"}{"SUBMITTED-C"} = 1;
    }
    if($response->get("SUBMITTED")) {
      push(@{$categorized_submissions{$query_and_document}{"SUBMITTED"}}, $response);
      $response->{ASSESSMENT}{"PRE-POLICY"}{SUBMITTED} = 1;
    }
    if($response->get("POOLED")) {
      # This response has been pooled and therefore should have been assessed
      # Find the corresponding assessment structure and bind it to this response
      push(@{$categorized_submissions{$query_and_document}{"POOLED"}}, $response);
      $response->{ASSESSMENT}{"PRE-POLICY"}{POOLED} = 1;
      my $assessment = $assessments->get("BY_KEY", "$query_id:$mention_span")
                         if $assessments->exists("$query_id:$mention_span");
      unless($assessment) {
        my $filename = $response->get("WHERE")->{FILENAME};
        my $linenum = $response->get("WHERE")->{LINENUM};
        my $line = $response->get("LINE");
        $logger->NIST_die("No assessment found for response\n $line\n in $filename (line#$linenum)\n");
      }
      $response->{ASSESSMENT_ENTRY} = $assessment;
      $fqec = $assessment->get("FQEC") || "N/A";
      if($assessment->get("ASSESSMENT") eq "CORRECT") {
        push(@{$categorized_submissions{$query_and_document}{"CORRECT"}}, $response);
        $response->{ASSESSMENT}{"PRE-POLICY"}{CORRECT} = 1;
        if($correct_found{$query_and_document}{$fqec}) {
          push(@{$categorized_submissions{$query_and_document}{"REDUNDANT"}}, $response);
          push(@{$categorized_submissions{$query_and_document}{"WRONG"}}, $response);
          $response->{ASSESSMENT}{"PRE-POLICY"}{REDUNDANT} = 1;
          $response->{ASSESSMENT}{"POST-POLICY"}{WRONG} = 1;
        }
        else {
          push(@{$categorized_submissions{$query_and_document}{"RIGHT"}}, $response);
          $correct_found{$query_and_document}{$fqec} = 1;
          $response->{ASSESSMENT}{"POST-POLICY"}{RIGHT} = 1;
        }
      }
      elsif($assessment->get("ASSESSMENT") eq "INCORRECT") {
        push(@{$categorized_submissions{$query_and_document}{"INCORRECT"}}, $response);
        $response->{ASSESSMENT}{"PRE-POLICY"}{INCORRECT} = 1;
        push(@{$categorized_submissions{$query_and_document}{"WRONG"}}, $response);
        $response->{ASSESSMENT}{"POST-POLICY"}{WRONG} = 1;
      }
      else{
        my $filename = $response->get("WHERE")->{FILENAME};
        my $linenum = $response->get("WHERE")->{LINENUM};
        my $line = $response->get("LINE");
        $logger->NIST_die("Unexpected value of assessment found for response\n $line\n in $filename (line#$linenum)\n");
      }
    }
    else {
      $response->{ASSESSMENT}{"POST-POLICY"}{"NOT-CONSIDERED"} = 1;
    }

    if ($response->{ASSESSMENT}{"POST-POLICY"}{RIGHT}) {
      $response->set("CORRECTNESS", "RIGHT");
      $response->set("CORRECTNESS_CODE", 1);
    }
    if ($response->{ASSESSMENT}{"POST-POLICY"}{WRONG}) {
      $response->set("CORRECTNESS", "WRONG");
      $response->set("CORRECTNESS_CODE", 0);
    }
    if ($response->{ASSESSMENT}{"POST-POLICY"}{IGNORE}) {
      $response->set("CORRECTNESS", "IGNORE");
      $response->set("CORRECTNESS_CODE", -1);
    }

    my $pre_policy = join(",", sort keys %{$response->{ASSESSMENT}{"PRE-POLICY"}});
    my $post_policy = join(",", sort keys %{$response->{ASSESSMENT}{"POST-POLICY"}});
    my $ag_cv = $responses->get("AG_CV", $response, $self->get("AG_CV_FIELDS"));
    my $line = "QUERYID=$query_id " .
                 "DOCUMENT_ID=$docid " .
                 "MENTION=$mention_span " .
                 "CLUSTER_ID=$cluster_id " .
                 "AG_CV=$ag_cv " .
                 "FQEC=$fqec " .
                 "PRE_POLICY_ASSESSMENT=$pre_policy " .
                 "POST_POLICY_ASSESSMENT=$post_policy\n";
    $logger->record_debug_information("RESPONSE_ASSESSMENT", $line, $response->get("WHERE"));
  }

  my %average_precision;
  foreach my $query_and_document(keys %selected_responses) {
    my ($query_id, $docid) = split(":", $query_and_document);
    my $num_ground_truth = scalar keys %{$ground_truth{$query_and_document}{FQEC_TO_MENTIONS}};
    my $max_num_ground_truth = $queries_to_score->get("BY_KEY", $query_id)->get("max_num_clusters");
    $average_precision{BESTCASE}{$query_and_document} = $self->get("AP", "BESTCASE", $num_ground_truth, $max_num_ground_truth, @{$selected_responses{$query_and_document}});
    $average_precision{WORSTCASE}{$query_and_document} = $self->get("AP", "WORSTCASE", $num_ground_truth, $max_num_ground_truth, @{$selected_responses{$query_and_document}});
    $average_precision{TRECEVAL}{$query_and_document} = $self->get("AP", "TRECEVAL", $num_ground_truth, $max_num_ground_truth, @{$selected_responses{$query_and_document}});
  }

  foreach my $query_id(sort $queries_to_score->get("ALL_KEYS")) {
    foreach my $docid(sort $docid_mappings->get("COREDOCS")->toarray()) {
      my $query_and_document = "$query_id:$docid";
      my $num_submitted_a = @{$categorized_submissions{$query_and_document}{"SUBMITTED-A"} || []};
      my $num_submitted_b = @{$categorized_submissions{$query_and_document}{"SUBMITTED-B"} || []};
      my $num_submitted = @{$categorized_submissions{$query_and_document}{"SUBMITTED"} || []};
      my $num_correct = @{$categorized_submissions{$query_and_document}{"CORRECT"} || []};
      my $num_incorrect = @{$categorized_submissions{$query_and_document}{"INCORRECT"} || []};
      my $num_right = @{$categorized_submissions{$query_and_document}{"RIGHT"} || []};
      my $num_wrong = @{$categorized_submissions{$query_and_document}{"WRONG"} || []};
      my $num_redundant = @{$categorized_submissions{$query_and_document}{"REDUNDANT"} || []};
      my $num_ignored = @{$categorized_submissions{$query_and_document}{"IGNORE"} || []};
      my $num_pooled = @{$categorized_submissions{$query_and_document}{"POOLED"} || []};
      my $num_ground_truth = scalar keys %{$ground_truth{$query_and_document}{FQEC_TO_MENTIONS}};
      my $ap_treceval = $average_precision{TRECEVAL}{$query_and_document} || 0;
      my $ap_bestcase = $average_precision{BESTCASE}{$query_and_document} || 0;
      my $ap_worstcase = $average_precision{WORSTCASE}{$query_and_document} || 0;
      my $score = ClassScore->new($logger, $runid, $query_id, $docid, $num_submitted_a, $num_submitted_b, $num_submitted, $num_correct, $num_incorrect, $num_right, $num_wrong, $num_redundant, $num_pooled, $num_ignored, $num_ground_truth, $ap_bestcase, $ap_worstcase, $ap_treceval);
      $scores->add($score, $query_and_document);
    }
  }
  $self->set("SCORES", $scores);
}

sub print_lines {
  my ($self, $program_output) = @_;
  $self->get("SCORES")->print_lines($program_output);
}

#####################################################################################
# ClassScoresPrinter
#####################################################################################

package ClassScoresPrinter;

use parent -norequire, 'Container', 'Super';

my @class_scorer_fields_to_print = (
  {NAME => 'EC',                 HEADER => 'QID/EC',   FORMAT => '%s',     JUSTIFY => 'L'},
  {NAME => 'DOCUMENT_ID',        HEADER => 'DocID',    FORMAT => '%s',     JUSTIFY => 'L'},
  {NAME => 'RUNID',              HEADER => 'RunID',    FORMAT => '%s',     JUSTIFY => 'L'},
  {NAME => 'NUM_GROUND_TRUTH',   HEADER => 'GT',       FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
#  {NAME => 'NUM_SUBMITTED_A',    HEADER => 'SubA',     FORMAT => '%4d',    JUSTIFY => 'R'},
#  {NAME => 'NUM_SUBMITTED_B',    HEADER => 'SubB',     FORMAT => '%4d',    JUSTIFY => 'R'},
  {NAME => 'NUM_SUBMITTED',      HEADER => 'Sub',      FORMAT => '%4d',    JUSTIFY => 'R'},
  {NAME => 'NUM_POOLED',         HEADER => 'Pooled',   FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_CORRECT',        HEADER => 'Correct',  FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_REDUNDANT',      HEADER => 'Dup',      FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_INCORRECT',      HEADER => 'Incrct',   FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_COUNTED',        HEADER => 'Cntd',     FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_RIGHT',          HEADER => 'Right',    FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_WRONG',          HEADER => 'Wrong',    FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_IGNORED',        HEADER => 'Ignrd',    FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
#  {NAME => 'PRECISION',          HEADER => 'Prec',     FORMAT => '%6.4f',  JUSTIFY => 'L'},
#  {NAME => 'RECALL',             HEADER => 'Recall',   FORMAT => '%6.4f',  JUSTIFY => 'L'},
#  {NAME => 'F1',                 HEADER => 'F1',       FORMAT => '%6.4f',  JUSTIFY => 'L'},
  {NAME => 'AVERAGE_PRECISION_BESTCASE',  HEADER => 'AP-B',   FORMAT => '%6.4f',  JUSTIFY => 'L'},
  {NAME => 'AVERAGE_PRECISION_WORSTCASE',  HEADER => 'AP-W',   FORMAT => '%6.4f',  JUSTIFY => 'L'},
  {NAME => 'AVERAGE_PRECISION_TRECEVAL',  HEADER => 'AP-T',   FORMAT => '%6.4f',  JUSTIFY => 'L'},
);

sub new {
  my ($class, $logger, $program_output) = @_;
  my $self = $class->SUPER::new($logger, 'ClassScore');
  $self->{__CLASS__} = 'ClassScoresPrinter';
  $self->{PROGRAM_OUTPUT} = $program_output;
  $self->{WIDTHS} = {map {$_->{NAME} => length($_->{HEADER})} @class_scorer_fields_to_print};
  $self->{LOGGER} = $logger;
  $self->{LINES} = [];
  @{$self->{FIELDS_TO_PRINT}} = @class_scorer_fields_to_print;
  bless($self, $class);
  $self;
}

sub get_SUMMARY {
  my ($self) = @_;
  my $logger = $self->get("LOGGER");
  my ($runid, $total_num_submitted_a, $total_num_submitted_b, $total_num_submitted, $total_num_correct, $total_num_incorrect, $total_num_right, $total_num_wrong, $total_num_redundant, $total_num_pooled, $total_num_ignored, $total_num_ground_truth, $map_bestcase, $map_worstcase, $map_treceval);
  my $total_num_counted_queries = 0;
  foreach my $score($self->toarray()) {
    my ($num_submitted_a, $num_submitted_b, $num_submitted, $num_correct, $num_incorrect, $num_right, $num_wrong, $num_redundant, $num_pooled, $num_ignored, $num_ground_truth, $ap_bestcase, $ap_worstcase, $ap_treceval)
      = map {$score->get($_)} qw(NUM_SUBMITTED_A NUM_SUBMITTED_B NUM_SUBMITTED NUM_CORRECT NUM_INCORRECT NUM_RIGHT NUM_WRONG NUM_REDUNDANT NUM_POOLED NUM_IGNORED NUM_GROUND_TRUTH AVERAGE_PRECISION_BESTCASE AVERAGE_PRECISION_WORSTCASE AVERAGE_PRECISION_TRECEVAL);
    $runid = $score->get("RUNID") unless $runid;
    $total_num_submitted += $num_submitted;
    $total_num_submitted_a += $num_submitted_a;
    $total_num_submitted_b += $num_submitted_b;
    $total_num_correct += $num_correct;
    $total_num_incorrect += $num_incorrect;
    $total_num_right += $num_right;
    $total_num_wrong += $num_wrong;
    $total_num_redundant += $num_redundant;
    $total_num_pooled += $num_pooled;
    $total_num_ignored += $num_ignored;
    $total_num_ground_truth += $num_ground_truth;
    $map_bestcase += $ap_bestcase;
    $map_worstcase += $ap_worstcase;
    $map_treceval += $ap_treceval;
    $total_num_counted_queries++ if $num_ground_truth;
  }
  $map_bestcase /= $total_num_counted_queries;
  $map_worstcase /= $total_num_counted_queries;
  $map_treceval /= $total_num_counted_queries;
  ClassScore->new($logger, $runid, "Summary", "", $total_num_submitted_a, $total_num_submitted_b, $total_num_submitted, $total_num_correct, $total_num_incorrect, $total_num_right, $total_num_wrong, $total_num_redundant, $total_num_pooled, $total_num_ignored, $total_num_ground_truth, $map_bestcase, $map_worstcase, $map_treceval);
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
  push(@scores, $self->get("SUMMARY"));
  foreach my $score (@scores) {
    my %elements_to_print;
    foreach my $field (@{$self->{FIELDS_TO_PRINT}}) {
      my $value = $score->get($field->{NAME});
      my $field_name = $field->{NAME};
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
# ClassScore
#####################################################################################

package ClassScore;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $runid, $query_id, $docid, $num_submitted_a, $num_submitted_b, $num_submitted, $num_correct, $num_incorrect, $num_right, $num_wrong, $num_redundant, $num_pooled, $num_ignored, $num_ground_truth, $ap_bestcase, $ap_worstcase, $ap_treceval) = @_;
  my $self = {
    __CLASS__ => 'ClassScore',
    AVERAGE_PRECISION_BESTCASE => $ap_bestcase,
    AVERAGE_PRECISION_WORSTCASE => $ap_worstcase,
    AVERAGE_PRECISION_TRECEVAL => $ap_treceval,
    EC => $query_id,
    DOCUMENT_ID => $docid,
    NUM_CORRECT => $num_correct,
    NUM_GROUND_TRUTH => $num_ground_truth,
    NUM_IGNORED => $num_ignored,
    NUM_INCORRECT => $num_incorrect,
    NUM_POOLED => $num_pooled,
    NUM_REDUNDANT => $num_redundant,
    NUM_RIGHT => $num_right,
    NUM_SUBMITTED => $num_submitted,
    NUM_SUBMITTED_A => $num_submitted_a,
    NUM_SUBMITTED_B => $num_submitted_b,
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

#####################################################################################
# ZeroHopScores
#####################################################################################

package ZeroHopScores;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $runid, $docid_mappings, $queries, $responses, $assessments, $queries_to_score) = @_;
  my $self = {
    __CLASS__ => 'ZeroHopScores',
    AG_CV_FIELDS => ["?link_cv"],
    AP_RANKING_SCORE_FIELDS => ["?j_cv"],
    ASSESSMENTS => $assessments,
    DOCID_MAPPINGS => $docid_mappings,
    QUERIES => $queries,
    QUERIES_TO_SCORE => $queries_to_score,
    RESPONSES => $responses,
    RUNID => $runid,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->score_responses();
  $self;
}

sub get_AP_RANKING_SCORE {
  my ($self, $response) = @_;
  $self->get("RESPONSES")->get("AG_CV", $response, $self->get("AP_RANKING_SCORE_FIELDS"));
}

sub get_AP {
  my ($self, $tie_breaking_criteria, $num_ground_truth, $max_num_ground_truth, @responses) = @_;
  return 0 unless $num_ground_truth;
  my %ranked_responses;
  my $rank = 1;
  my $correct_at_rank = 0;
  my $sum_precision = 0;
  if($tie_breaking_criteria eq "BESTCASE") {
    @responses = sort {$self->get("AP_RANKING_SCORE", $b) <=> $self->get("AP_RANKING_SCORE", $a) ||
                              $a->get("CORRECTNESS") cmp $b->get("CORRECTNESS")} @responses;
  }
  elsif($tie_breaking_criteria eq "WORSTCASE") {
    @responses = sort {$self->get("AP_RANKING_SCORE", $b) <=> $self->get("AP_RANKING_SCORE", $a) ||
                              $b->get("CORRECTNESS") cmp $a->get("CORRECTNESS")} @responses;
  }
  elsif($tie_breaking_criteria eq "TRECEVAL") {
    @responses = sort {$self->get("AP_RANKING_SCORE", $b) <=> $self->get("AP_RANKING_SCORE", $a) ||
                              $b->get("VALUE_PROVENANCE_TRIPLE") cmp $a->get("VALUE_PROVENANCE_TRIPLE")} @responses;
  }
  else {
    $self->get("LOGGER")->NIST_die("Unknown tie breaking criteria: $tie_breaking_criteria");
  }
  foreach my $response(@responses) {
    my $correctness = $response->get("CORRECTNESS");
    next if $correctness eq "IGNORE";
    $ranked_responses{$rank} = $response;
    if($correctness eq "RIGHT" && $rank < $max_num_ground_truth) {
      $correct_at_rank++;
      $sum_precision += $correct_at_rank/$rank;
    }
    my ($query_id, $docid, $mention_span, $run_id)
      = map {$response->get($_)} qw(QUERY_ID DOCUMENT_ID VALUE_PROVENANCE_TRIPLE RUN_ID);
    my $score = $self->get("AP_RANKING_SCORE", $response);
    my $line = "$tie_breaking_criteria $query_id $docid $mention_span $rank $score $run_id $correctness";
    $self->get("LOGGER")->record_debug_information("AP_SUBMISSION_LINE", $line, $response->get("WHERE"));
    $rank++;
  }

  my $ap = $sum_precision / (($num_ground_truth <= $max_num_ground_truth) ? $num_ground_truth : $max_num_ground_truth);
  $self->get("LOGGER")->NIST_die("AP > 1") if $ap > 1;
  $ap;
}

sub score_responses {
  my ($self) = @_;
  my ($logger, $runid, $docid_mappings, $queries, $responses, $assessments, $queries_to_score)
    = map {$self->get($_)} qw(LOGGER RUNID DOCID_MAPPINGS QUERIES RESPONSES ASSESSMENTS QUERIES_TO_SCORE);
  my $scores = ZeroHopScoresPrinter->new($logger);

  my %ground_truth;
  foreach my $assessment_entry($assessments->toarray()) {
    my ($assessment, $docid, $mention_span, $reference_kbid) = 
      map {$assessment_entry->get($_)} qw(ASSESSMENT DOCUMENT_ID MENTION_SPAN REFERENCE_KBID);
    $mention_span = "$docid:$mention_span";
    $ground_truth{$reference_kbid}{$docid}{$mention_span} = 1 if $assessment eq "CORRECT";
  }

  my %candidate_responses;
  foreach my $response($responses->get("RESPONSES")->toarray()) {
    my ($query_id, $cluster_rank, $docid, $mention_span, $reference_kbid)
      = map {$response->get($_)} qw(QUERY_ID CLUSTER_RANK DOCUMENT_ID VALUE_PROVENANCE_TRIPLE QUERY_LINK_TARGET_IN_RESPONSE);
    next unless $queries_to_score->exists($query_id);
    my $max_cluster_rank = $queries_to_score->get("BY_KEY", $query_id)->get("max_num_clusters");
    $response->set("SUBMITTED-A", 1);
    next if ($cluster_rank > $max_cluster_rank);
    $response->set("SUBMITTED-B", 1);
    push(@{$candidate_responses{$query_id}}, $response);
  }

  my %selected_responses;
  foreach my $query_id(keys %candidate_responses) {
    my %responses_per_document;
    foreach my $response(@{$candidate_responses{$query_id}}) {
      if(exists $responses_per_document{$response->get("DOCUMENT_ID")}) {
        my $runid = $response->get("RUN_ID");
        my $run_and_query = "$runid:$query_id";
        my $cluster_id = $response->get("CLUSTER_ID");
        $logger->record_problem("MULTIPLE_INFORMATIVE_JUSTIFICATIONS_PER_DOCUMENT", $run_and_query, $cluster_id, $response->get("DOCUMENT_ID"), $response->get("WHERE"));
        $responses_per_document{$response->get("DOCUMENT_ID")} = $response
          if($response->get("JUSTIFICATION_CONFIDENCE") > $responses_per_document{$response->get("DOCUMENT_ID")}->get("JUSTIFICATION_CONFIDENCE"));
      }
      else {
        $responses_per_document{$response->get("DOCUMENT_ID")} = $response;
      }
    }
    my $i = 0;
    foreach my $response(sort {$responses->get("AG_CV", $b, $self->get("AG_CV_FIELDS")) <=> $responses->get("AG_CV", $a, $self->get("AG_CV_FIELDS"))
                                    || $a->get("VALUE_PROVENANCE_TRIPLE") cmp $b->get("VALUE_PROVENANCE_TRIPLE")}
                              values %responses_per_document) {
      my $max_num_informative_mentions = $queries_to_score->get("BY_KEY", $response->get("QUERY_ID"))->get("max_num_informative_mentions");
      $response->set("SUBMITTED", 1);
      next if $i == $max_num_informative_mentions;
      next unless $docid_mappings->get("COREDOCS")->exists($response->get("DOCUMENT_ID"));
      push(@{$selected_responses{$query_id}}, $response);
      $response->set("POOLED", 1);
      $i++;
    }
  }
  
  my %categorized_submissions;
  my %correct_found;
  my %incorrect_found;
  my %document_based_assessments_assigned;
  foreach my $response($responses->get("RESPONSES")->toarray()) {
    my ($query_id, $docid, $cluster_id, $mention_span, $reference_kbid)
      = map {$response->get($_)} qw(QUERY_ID DOCUMENT_ID CLUSTER_ID VALUE_PROVENANCE_TRIPLE QUERY_LINK_TARGET_IN_RESPONSE);
    if($response->get("SUBMITTED-A")) {
      push(@{$categorized_submissions{$query_id}{"SUBMITTED-A"}}, $response);
      $response->{ASSESSMENT}{"PRE-POLICY"}{"SUBMITTED-A"} = 1;
    }
    if($response->get("SUBMITTED-B")) {
      push(@{$categorized_submissions{$query_id}{"SUBMITTED-B"}}, $response);
      $response->{ASSESSMENT}{"PRE-POLICY"}{"SUBMITTED-B"} = 1;
    }
    if($response->get("SUBMITTED")) {
      push(@{$categorized_submissions{$query_id}{"SUBMITTED"}}, $response);
      $response->{ASSESSMENT}{"PRE-POLICY"}{SUBMITTED} = 1;
    }
    if($response->get("POOLED")) {
      # This response has been pooled and therefore should have been assessed
      # Find the corresponding assessment structure and bind it to this response
      push(@{$categorized_submissions{$query_id}{"POOLED"}}, $response);
      $response->{ASSESSMENT}{"PRE-POLICY"}{POOLED} = 1;
      my $assessment = $assessments->get("BY_KEY", "$reference_kbid:$mention_span") if $assessments->exists("$reference_kbid:$mention_span");
      unless($assessment) {
        my $filename = $response->get("WHERE")->{FILENAME};
        my $linenum = $response->get("WHERE")->{LINENUM};
        my $line = $response->get("LINE");
        die "No assessment found for response\n $line\n in $filename (line#$linenum)\n";
      }
      $response->{ASSESSMENT_ENTRY} = $assessment;
      if($assessment->get("ASSESSMENT") eq "CORRECT") {
        push(@{$categorized_submissions{$query_id}{"CORRECT"}}, $response);
        $response->{ASSESSMENT}{"PRE-POLICY"}{CORRECT} = 1;
        if($correct_found{$query_id}{$mention_span}) {
          push(@{$categorized_submissions{$query_id}{"IGNORE"}}, $response);
          push(@{$categorized_submissions{$query_id}{"REDUNDANT"}}, $response);
          $response->{ASSESSMENT}{"POST-POLICY"}{IGNORE} = 1;
          $response->{ASSESSMENT}{"PRE-POLICY"}{REDUNDANT} = 1;
        }
        else {
          push(@{$categorized_submissions{$query_id}{"RIGHT"}}, $response);
          $correct_found{$query_id}{$mention_span} = 1;
          $response->{ASSESSMENT}{"POST-POLICY"}{RIGHT} = 1;
          $document_based_assessments_assigned{$query_id}{$mention_span} = 1;
        }
      }
      elsif($assessment->get("ASSESSMENT") eq "INCORRECT") {
        push(@{$categorized_submissions{$query_id}{"INCORRECT"}}, $response);
        $response->{ASSESSMENT}{"PRE-POLICY"}{INCORRECT} = 1;
        if($incorrect_found{$query_id}{$mention_span}) {
          push(@{$categorized_submissions{$query_id}{"IGNORE"}}, $response);
          $response->{ASSESSMENT}{"POST-POLICY"}{IGNORE} = 1;
        }
        else {
          push(@{$categorized_submissions{$query_id}{"WRONG"}}, $response);
          $response->{ASSESSMENT}{"POST-POLICY"}{WRONG} = 1;
          $document_based_assessments_assigned{$query_id}{$mention_span} = 0 unless $document_based_assessments_assigned{$query_id}{$mention_span};
        }
      }
      else{
        my $filename = $response->get("WHERE")->{FILENAME};
        my $linenum = $response->get("WHERE")->{LINENUM};
        my $line = $response->get("LINE");
        $logger->NIST_die("Unexpected value of assessment found for response\n $line\n in $filename (line#$linenum)\n");
      }
    }
    else {
      if($response->get("SUBMITTED")) {
        push(@{$categorized_submissions{$query_id}{"NOTPOOLED"}}, $response);
        $response->{ASSESSMENT}{"PRE-POLICY"}{NOTPOOLED} = 1;
      }
      $response->{ASSESSMENT}{"POST-POLICY"}{"NOT-CONSIDERED"} = 1;
    }

    $response->set("CORRECTNESS", "RIGHT") if $response->{ASSESSMENT}{"POST-POLICY"}{RIGHT};
    $response->set("CORRECTNESS", "WRONG") if $response->{ASSESSMENT}{"POST-POLICY"}{WRONG};
    $response->set("CORRECTNESS", "IGNORE") if $response->{ASSESSMENT}{"POST-POLICY"}{IGNORE};

    my $pre_policy = join(",", sort keys %{$response->{ASSESSMENT}{"PRE-POLICY"}});
    my $post_policy = join(",", sort keys %{$response->{ASSESSMENT}{"POST-POLICY"}});
    my $ag_cv = $responses->get("AG_CV", $response, $self->get("AG_CV_FIELDS"));
    my $line = "QUERYID=$query_id " .
                 "KBID=$reference_kbid " .
                 "MENTION=$mention_span " .
                 "CLUSTER_ID=$cluster_id " .
                 "AG_CV=$ag_cv " .
                 "PRE_POLICY_ASSESSMENT=$pre_policy " .
                 "POST_POLICY_ASSESSMENT=$post_policy\n";
    $logger->record_debug_information("RESPONSE_ASSESSMENT", $line, $response->get("WHERE"));
  }

  my %average_precision;
  foreach my $query_id(keys %selected_responses) {
    my $node_id = $queries->get("QUERY", $query_id)->get("REFERENCE_KBID");
    my $num_ground_truth = keys %{$ground_truth{$node_id}};
    my $max_num_ground_truth = $queries_to_score->get("BY_KEY", $query_id)->get("max_num_informative_mentions");
    $average_precision{BESTCASE}{$query_id} = $self->get("AP", "BESTCASE", $num_ground_truth, $max_num_ground_truth, @{$selected_responses{$query_id}});
    $average_precision{WORSTCASE}{$query_id} = $self->get("AP", "WORSTCASE", $num_ground_truth, $max_num_ground_truth, @{$selected_responses{$query_id}});
    $average_precision{TRECEVAL}{$query_id} = $self->get("AP", "TRECEVAL", $num_ground_truth, $max_num_ground_truth, @{$selected_responses{$query_id}});
  }

  foreach my $query_id(sort $queries_to_score->get("ALL_KEYS")) {
    my $node_id = $queries->get("QUERY", $query_id)->get("REFERENCE_KBID");
    my $num_submitted_a = @{$categorized_submissions{$query_id}{"SUBMITTED-A"} || []};
    my $num_submitted_b = @{$categorized_submissions{$query_id}{"SUBMITTED-B"} || []};
    my $num_submitted = @{$categorized_submissions{$query_id}{"SUBMITTED"} || []};
    my $num_correct = @{$categorized_submissions{$query_id}{"CORRECT"} || []};
    my $num_incorrect = @{$categorized_submissions{$query_id}{"INCORRECT"} || []};
    my $num_right = @{$categorized_submissions{$query_id}{"RIGHT"} || []};
    my $num_wrong = @{$categorized_submissions{$query_id}{"WRONG"} || []};
    my $num_redundant = @{$categorized_submissions{$query_id}{"REDUNDANT"} || []};
    my $num_ignored = @{$categorized_submissions{$query_id}{"IGNORE"} || []};
    my $num_pooled = @{$categorized_submissions{$query_id}{"POOLED"} || []};
    my $num_ground_truth = keys %{$ground_truth{$node_id}};
    my $ap_treceval = $average_precision{TRECEVAL}{$query_id} || 0;
    my $ap_bestcase = $average_precision{BESTCASE}{$query_id} || 0;
    my $ap_worstcase = $average_precision{WORSTCASE}{$query_id} || 0;
    my $score = ZeroHopScore->new($logger, $runid, $query_id, $node_id, $num_submitted_a, $num_submitted_b, $num_submitted, $num_correct, $num_incorrect, $num_right, $num_wrong, $num_redundant, $num_pooled, $num_ignored, $num_ground_truth, $ap_bestcase, $ap_worstcase, $ap_treceval);
    $scores->add($score, $query_id);
  }
  $self->set("SCORES", $scores);
}

sub print_lines {
  my ($self, $program_output) = @_;
  $self->get("SCORES")->print_lines($program_output);
}

#####################################################################################
# ZeroHopScoresPrinter
#####################################################################################

package ZeroHopScoresPrinter;

use parent -norequire, 'Container', 'Super';

my @zerohop_scorer_fields_to_print = (
  {NAME => 'EC',                 HEADER => 'QID/EC',   FORMAT => '%s',     JUSTIFY => 'L'},
#  {NAME => 'NODEID',             HEADER => 'Node',     FORMAT => '%s',     JUSTIFY => 'L'},
  {NAME => 'RUNID',              HEADER => 'RunID',    FORMAT => '%s',     JUSTIFY => 'L'},
  {NAME => 'NUM_GROUND_TRUTH',   HEADER => 'GT',       FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
#  {NAME => 'NUM_SUBMITTED_A',    HEADER => 'SubA',     FORMAT => '%4d',    JUSTIFY => 'R'},
#  {NAME => 'NUM_SUBMITTED_B',    HEADER => 'SubB',     FORMAT => '%4d',    JUSTIFY => 'R'},
  {NAME => 'NUM_SUBMITTED',      HEADER => 'Sub',      FORMAT => '%4d',    JUSTIFY => 'R'},
  {NAME => 'NUM_POOLED',         HEADER => 'Pooled',   FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_CORRECT',        HEADER => 'Correct',  FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_REDUNDANT',      HEADER => 'Dup',      FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_INCORRECT',      HEADER => 'Incrct',   FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_COUNTED',        HEADER => 'Cntd',     FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_RIGHT',          HEADER => 'Right',    FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_WRONG',          HEADER => 'Wrong',    FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_IGNORED',        HEADER => 'Ignrd',    FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
#  {NAME => 'PRECISION',          HEADER => 'Prec',     FORMAT => '%6.4f',  JUSTIFY => 'L'},
#  {NAME => 'RECALL',             HEADER => 'Recall',   FORMAT => '%6.4f',  JUSTIFY => 'L'},
#  {NAME => 'F1',                 HEADER => 'F1',       FORMAT => '%6.4f',  JUSTIFY => 'L'},
  {NAME => 'AVERAGE_PRECISION_BESTCASE',  HEADER => 'AP-B',   FORMAT => '%6.4f',  JUSTIFY => 'L'},
  {NAME => 'AVERAGE_PRECISION_WORSTCASE',  HEADER => 'AP-W',   FORMAT => '%6.4f',  JUSTIFY => 'L'},
  {NAME => 'AVERAGE_PRECISION_TRECEVAL',  HEADER => 'AP-T',   FORMAT => '%6.4f',  JUSTIFY => 'L'},
);

sub new {
  my ($class, $logger, $program_output) = @_;
  my $self = $class->SUPER::new($logger, 'Score');
  $self->{__CLASS__} = 'ZeroHopScoresPrinter';
  $self->{PROGRAM_OUTPUT} = $program_output;
  $self->{WIDTHS} = {map {$_->{NAME} => length($_->{HEADER})} @zerohop_scorer_fields_to_print};
  $self->{LOGGER} = $logger;
  $self->{LINES} = [];
  @{$self->{FIELDS_TO_PRINT}} = @zerohop_scorer_fields_to_print;
  bless($self, $class);
  $self;
}

sub get_SUMMARY {
  my ($self) = @_;
  my $logger = $self->get("LOGGER");
  my ($runid, $total_num_submitted_a, $total_num_submitted_b, $total_num_submitted, $total_num_correct, $total_num_incorrect, $total_num_right, $total_num_wrong, $total_num_redundant, $total_num_pooled, $total_num_ignored, $total_num_ground_truth, $map_bestcase, $map_worstcase, $map_treceval);
  my $total_num_counted_queries = 0;
  foreach my $score($self->toarray()) {
    my ($num_submitted_a, $num_submitted_b, $num_submitted, $num_correct, $num_incorrect, $num_right, $num_wrong, $num_redundant, $num_pooled, $num_ignored, $num_ground_truth, $ap_bestcase, $ap_worstcase, $ap_treceval)
      = map {$score->get($_)} qw(NUM_SUBMITTED_A NUM_SUBMITTED_B NUM_SUBMITTED NUM_CORRECT NUM_INCORRECT NUM_RIGHT NUM_WRONG NUM_REDUNDANT NUM_POOLED NUM_IGNORED NUM_GROUND_TRUTH AVERAGE_PRECISION_BESTCASE AVERAGE_PRECISION_WORSTCASE AVERAGE_PRECISION_TRECEVAL);
    $runid = $score->get("RUNID") unless $runid;
    $total_num_submitted += $num_submitted;
    $total_num_submitted_a += $num_submitted_a;
    $total_num_submitted_b += $num_submitted_b;
    $total_num_correct += $num_correct;
    $total_num_incorrect += $num_incorrect;
    $total_num_right += $num_right;
    $total_num_wrong += $num_wrong;
    $total_num_redundant += $num_redundant;
    $total_num_pooled += $num_pooled;
    $total_num_ignored += $num_ignored;
    $total_num_ground_truth += $num_ground_truth;
    $map_bestcase += $ap_bestcase;
    $map_worstcase += $ap_worstcase;
    $map_treceval += $ap_treceval;
    $total_num_counted_queries++ if $num_ground_truth;
  }
  $map_bestcase /= $total_num_counted_queries;
  $map_worstcase /= $total_num_counted_queries;
  $map_treceval /= $total_num_counted_queries;
  ZeroHopScore->new($logger, $runid, "Summary", "", $total_num_submitted_a, $total_num_submitted_b, $total_num_submitted, $total_num_correct, $total_num_incorrect, $total_num_right, $total_num_wrong, $total_num_redundant, $total_num_pooled, $total_num_ignored, $total_num_ground_truth, $map_bestcase, $map_worstcase, $map_treceval);
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
  push(@scores, $self->get("SUMMARY"));
  foreach my $score (@scores) {
    my %elements_to_print;
    foreach my $field (@{$self->{FIELDS_TO_PRINT}}) {
      my $value = $score->get($field->{NAME});
      my $field_name = $field->{NAME};
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
# ZeroHopScore
#####################################################################################

package ZeroHopScore;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $runid, $query_id, $node_id, $num_submitted_a, $num_submitted_b, $num_submitted, $num_correct, $num_incorrect, $num_right, $num_wrong, $num_redundant, $num_pooled, $num_ignored, $num_ground_truth, $ap_bestcase, $ap_worstcase, $ap_treceval) = @_;
  my $self = {
    __CLASS__ => 'ZeroHopScore',
    AVERAGE_PRECISION_BESTCASE => $ap_bestcase,
    AVERAGE_PRECISION_WORSTCASE => $ap_worstcase,
    AVERAGE_PRECISION_TRECEVAL => $ap_treceval,
    EC => $query_id,
    NODEID => $node_id,
    NUM_CORRECT => $num_correct,
    NUM_GROUND_TRUTH => $num_ground_truth,
    NUM_IGNORED => $num_ignored,
    NUM_INCORRECT => $num_incorrect,
    NUM_POOLED => $num_pooled,
    NUM_REDUNDANT => $num_redundant,
    NUM_RIGHT => $num_right,
    NUM_SUBMITTED => $num_submitted,
    NUM_SUBMITTED_A => $num_submitted_a,
    NUM_SUBMITTED_B => $num_submitted_b,
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

#sub get_PRECISION {
#  my ($self) = @_;
#  $self->get("NUM_COUNTED") ? $self->get("NUM_RIGHT")/($self->get("NUM_COUNTED")) : 0;
#}
#
#sub get_RECALL {
#  my ($self) = @_;
#  $self->get("NUM_GROUND_TRUTH") ? $self->get("NUM_RIGHT")/($self->get("NUM_GROUND_TRUTH")) : 0;
#}
#
#sub get_F1 {
#  my ($self) = @_;
#  my $precision = $self->get("PRECISION");
#  my $recall = $self->get("RECALL");
#  ($precision + $recall) ? 2*$precision*$recall/($precision + $recall) : 0;
#}

#####################################################################################
# GraphScores
#####################################################################################

package GraphScores;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $runid, $docid_mappings, $queries, $salient_edges, $responses, $assessments, $queries_to_score, $strategy) = @_;
  my $self = {
    __CLASS__ => 'GraphScores',
    ASSESSMENTS => $assessments,
    DOCID_MAPPINGS => $docid_mappings,
    QUERIES => $queries,
    SALIENT_EDGES => $salient_edges,
    QUERIES_TO_SCORE => $queries_to_score,
    FRAMES => Frames->new($logger, $queries_to_score, $queries->get("TASK_AND_TYPE_CODE")),
    RESPONSES => $responses,
    RUNID => $runid,
    STRATEGY => $strategy,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->score_responses();
  $self;
}

sub score_responses {
  my ($self) = @_;
  my $strategy = uc($self->get("STRATEGY"));
  my $code = $self->get("QUERIES")->get("TASK_AND_TYPE_CODE");
  my $task = "TASK1" if $code eq "TA1_GR";
  $task = "TASK2" if $code eq "TA2_GR";
  my $method = $self->can("score_responses_$task\_$strategy");
  $self->get("LOGGER")->NIST_die("Unexpected value of scoring strategy $strategy") unless $method;
  $method->($self);
}


sub score_responses_TASK1_DEFAULT {
  my ($self) = @_;
  $self->score_responses_TASK1_STRATEGY1();
}

sub score_responses_TASK1_STRATEGY1 {
  my ($self) = @_;
  my ($logger, $runid, $docid_mappings, $queries, $salient_edges, $responses, $assessments, $queries_to_score)
    = map {$self->get($_)} qw(LOGGER RUNID DOCID_MAPPINGS QUERIES SALIENT_EDGES RESPONSES ASSESSMENTS QUERIES_TO_SCORE);
  my $scores = Task1GraphScoresStrategy1Printer->new($logger);

  # Gather ground truth for Strategy 1A
  # For each single edge query, how many unique (real-world - as determined by LDC's equivalence classes)
  # edges were correct?
  my %ground_truth;
  foreach my $entry($assessments->toarray()) {
    my ($subject, $predicate, $object, $docid, $correctness, $linkability, $predicate_justification, 
          $object_justification) =
      map {$entry->get($_)}
        qw(SUBJECT_FQEC
           PREDICATE
           OBJECT_FQEC
           DOCUMENT_ID
           PREDICATE_JUSTIFICATION_CORRECTNESS
           OBJECT_LINKABILITY
           PREDICATE_JUSTIFICATION
           OBJECT_JUSTIFICATION);
    $predicate_justification = join(";", map {"$docid:".$_} split(";", $predicate_justification));
    $object_justification = "$docid:$object_justification";
    my $key = "$predicate:$predicate_justification:$object_justification";
    my $edge_fqec = "$subject:$predicate:$object";
    $logger->NIST_die("Duplicate assessment for key $key") if $ground_truth{"STRATEGY-1A"}{ENTRIES_BY_KEY}{$key};
    $ground_truth{"STRATEGY-1A"}{ENTRIES_BY_KEY}{$key} = $entry;
    next unless ($correctness eq "CORRECT" && $linkability eq "YES");
    my @queries = $queries->get("MATCHING_QUERIES", (PREDICATE=>$predicate));
    unless (@queries) {
      $logger->record_debug_information("NO_QUERY_FOR_ASSESSNENT_ITEM", $entry->get("LINE"), $entry->get("WHERE"));
      next;
    }
    $entry->set("QUERIES", @queries);
    foreach my $query(@queries) {
      my $query_id = $query->get("QUERYID");
      my $query_and_document = "$query_id:$docid";
      push(@{$ground_truth{"STRATEGY-1A"}{ENTRIES_BY_QUERYDOC_AND_EDGEFQEC}{$query_and_document}{$edge_fqec}}, $entry);
      my $line = "DETAIL QUERYID=$query_id " .
                   "DOCUMENT=$docid " .
                   "EDGE_FQEC=$edge_fqec " .
                   "SUBJECT=$subject " .
                   "PREDICATE=$predicate " .
                   "OBJECT=$object";
      $logger->record_debug_information("GROUND_TRUTH", $line, $entry->get("WHERE"));
    }
  }

  my %candidate_responses;
  foreach my $response($responses->get("RESPONSES")->toarray()) {
    my ($query_id, $docid, $predicate_justification, $object_justification, $rank) =
      map {$response->get($_)}
        qw(QUERY_ID
           DOCUMENT_ID
           EDGE_PROVENANCE_TRIPLES
           OBJECT_VALUE_PROVENANCE_TRIPLE
           RANK);
    my $query_and_document = "$query_id:$docid";
    next unless $docid_mappings->get("COREDOCS")->exists($docid);
    next unless $queries_to_score->exists($query_id);
    next unless $ground_truth{"STRATEGY-1A"}{ENTRIES_BY_QUERYDOC_AND_EDGEFQEC}{$query_and_document};
    my $max_rank = $queries_to_score->get("BY_KEY", $query_id)->get("depth");
    $response->set("STRATEGY-1A-SUBMITTED", 1) if $rank;
    $response->set("STRATEGY-1A-POOLED", 1) if ($rank && $rank <= $max_rank);
    push(@{$candidate_responses{$query_and_document}}, $response) if $rank;
  }

  # categorize submissions
  my %categorized_submissions;
  my %correct_found;
  foreach my $query_and_document(sort keys %candidate_responses) {
    foreach my $response(@{$candidate_responses{$query_and_document}}) {
      my ($query_id, $docid, $predicate_justification, $object_justification) =
        map {$response->get($_)}
          qw(QUERY_ID
             DOCUMENT_ID
             EDGE_PROVENANCE_TRIPLES
             OBJECT_VALUE_PROVENANCE_TRIPLE);
      my $predicate = $response->get("QUERY")->get("PREDICATE");
      if($response->get("STRATEGY-1A-SUBMITTED")) {
        push(@{$categorized_submissions{"STRATEGY-1A"}{$query_and_document}{SUBMITTED}}, $response);
        $response->{ASSESSMENT}{"STRATEGY-1A"}{"PRE-POLICY"}{SUBMITTED} = 1;
      }
      if($response->get("STRATEGY-1A-POOLED")) {
        push(@{$categorized_submissions{"STRATEGY-1A"}{$query_and_document}{POOLED}}, $response);
        $response->{ASSESSMENT}{"STRATEGY-1A"}{"PRE-POLICY"}{POOLED} = 1;
        my $key = "$predicate:$predicate_justification:$object_justification";
        my $assessment = $ground_truth{"STRATEGY-1A"}{ENTRIES_BY_KEY}{$key};
        $logger->NIST_die("Assessment not found for key $key") unless $assessment;
        $response->set("ASSESSMENT_ENTRY", $assessment);
        if($assessment->get("PREDICATE_JUSTIFICATION_CORRECTNESS") eq "CORRECT") {
          push(@{$categorized_submissions{"STRATEGY-1A"}{$query_and_document}{CORRECT}}, $response);
          $response->{ASSESSMENT}{"STRATEGY-1A"}{"PRE-POLICY"}{CORRECT} = 1;
          if($assessment->get("OBJECT_LINKABILITY") eq "YES") {
            push(@{$categorized_submissions{"STRATEGY-1A"}{$query_and_document}{PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT}}, $response);
            $response->{ASSESSMENT}{"STRATEGY-1A"}{"PRE-POLICY"}{PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT} = 1;
            # response is either RIGHT or REDUNDANT because it met both the conditions given below:
            #  (1) correct predicate justification, and
            #  (2) predicate justification is linkable to object justification
            my ($subject, $predicate, $object) = map {$assessment->get($_)} qw(SUBJECT_FQEC PREDICATE OBJECT_FQEC);
            my $edge_string = join("\t", ($subject, $predicate, "LDC2019E43:".$object));
            if($correct_found{"STRATEGY-1A"}{$query_and_document}{$edge_string}) {
              push(@{$categorized_submissions{"STRATEGY-1A"}{$query_and_document}{REDUNDANT}}, $response);
              $response->{ASSESSMENT}{"STRATEGY-1A"}{"PRE-POLICY"}{REDUNDANT} = 1;
              push(@{$categorized_submissions{"STRATEGY-1A"}{$query_and_document}{IGNORE}}, $response);
              $response->{ASSESSMENT}{"STRATEGY-1A"}{"POST-POLICY"}{IGNORE} = 1;
            }
            else{
              push(@{$categorized_submissions{"STRATEGY-1A"}{$query_and_document}{RIGHT}}, $response);
              $response->{ASSESSMENT}{"STRATEGY-1A"}{"POST-POLICY"}{RIGHT} = 1;
              $correct_found{"STRATEGY-1A"}{$query_and_document}{$edge_string} = 1;
              if(exists $ground_truth{"STRATEGY-1B"}{SALIENT_EDGES}{$query_id}{$edge_string}) {
                $response->{ASSESSMENT}{"STRATEGY-1B"}{"POST-POLICY"}{SALIENT} = 1;
                push(@{$categorized_submissions{"STRATEGY-1B"}{$query_and_document}{SALIENT}}, $response);
              }
            }
          }
          else {
            push(@{$categorized_submissions{"STRATEGY-1A"}{$query_and_document}{WRONG}}, $response);
            $response->{ASSESSMENT}{"STRATEGY-1A"}{"POST-POLICY"}{WRONG} = 1;
          }
        }
        elsif($assessment->get("PREDICATE_JUSTIFICATION_CORRECTNESS") eq "INCORRECT") {
          push(@{$categorized_submissions{"STRATEGY-1A"}{$query_and_document}{INCORRECT}}, $response);
          $response->{ASSESSMENT}{"STRATEGY-1A"}{"PRE-POLICY"}{INCORRECT} = 1;
          push(@{$categorized_submissions{"STRATEGY-1A"}{$query_and_document}{WRONG}}, $response);
          $response->{ASSESSMENT}{"STRATEGY-1A"}{"POST-POLICY"}{WRONG} = 1;
        }
        else{
          my $filename = $response->get("WHERE")->{FILENAME};
          my $linenum = $response->get("WHERE")->{LINENUM};
          my $line = $response->get("LINE");
          $logger->NIST_die("Unexpected value of assessment found for response\n $line\n in $filename (line#$linenum)\n");
        }
      }
      else {
        $response->{ASSESSMENT}{"STRATEGY-1A"}{"PRE-POLICY"}{NOTPOOLED} = 1;
        $response->{ASSESSMENT}{"STRATEGY-1A"}{"POST-POLICY"}{"NOT-CONSIDERED"} = 1;
      }
      my $pre_policy = join(",", sort keys %{$response->{ASSESSMENT}{"STRATEGY-1A"}{"PRE-POLICY"}});
      my $post_policy = join(",", sort keys %{$response->{ASSESSMENT}{"STRATEGY-1A"}{"POST-POLICY"}});
      my $line = "QUERYID=$query_id " .
                   "DOCID=$docid " .
                   "PREDICATE_JUSTIFICATION=$predicate_justification " .
                   "OBJECT_JUSTIFICATION=$object_justification " .
                   "PRE_POLICY_ASSESSMENT=$pre_policy " .
                   "POST_POLICY_ASSESSMENT=$post_policy";
      $logger->record_debug_information("RESPONSE_ASSESSMENT", $line, $response->get("WHERE"));
    }
  }

  foreach my $query_id(sort $queries_to_score->get("ALL_KEYS")) {
    foreach my $docid(sort $docid_mappings->get("COREDOCS")->toarray()) {
      my $query_and_document = "$query_id:$docid";
      my $num_submitted_1a = @{$categorized_submissions{"STRATEGY-1A"}{$query_and_document}{SUBMITTED} || []};
      my $num_correct_1a = @{$categorized_submissions{"STRATEGY-1A"}{$query_and_document}{"CORRECT"} || []};
      my $num_predicate_justification_linkable_to_object_1a = @{$categorized_submissions{"STRATEGY-1A"}{$query_and_document}{"PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT"} || []};
      my $num_incorrect_1a = @{$categorized_submissions{"STRATEGY-1A"}{$query_and_document}{"INCORRECT"} || []};
      my $num_right_1a = @{$categorized_submissions{"STRATEGY-1A"}{$query_and_document}{"RIGHT"} || []};
      my $num_wrong_1a = @{$categorized_submissions{"STRATEGY-1A"}{$query_and_document}{"WRONG"} || []};
      my $num_redundant_1a = @{$categorized_submissions{"STRATEGY-1A"}{$query_and_document}{"REDUNDANT"} || []};
      my $num_ignored_1a = @{$categorized_submissions{"STRATEGY-1A"}{$query_and_document}{"IGNORE"} || []};
      my $num_pooled_1a = @{$categorized_submissions{"STRATEGY-1A"}{$query_and_document}{"POOLED"} || []};
      my $num_ground_truth_1a = keys %{$ground_truth{"STRATEGY-1A"}{ENTRIES_BY_QUERYDOC_AND_EDGEFQEC}{$query_and_document}};
      my $depth = $queries_to_score->get("BY_KEY", $query_id)->get("depth");
      my $num_ground_truth_1a_counted = $num_ground_truth_1a > $depth ? $depth : $num_ground_truth_1a;
      my $score = Task1GraphScoreStrategy1->new($logger,
                                    $runid,
                                    $query_id,
                                    $docid,
                                    $num_submitted_1a,
                                    $num_correct_1a,
                                    $num_predicate_justification_linkable_to_object_1a,
                                    $num_incorrect_1a,
                                    $num_right_1a,
                                    $num_wrong_1a,
                                    $num_redundant_1a,
                                    $num_pooled_1a,
                                    $num_ignored_1a,
                                    $num_ground_truth_1a,
                                    $num_ground_truth_1a_counted);
      $scores->add($score, $query_and_document);
    }
    $self->set("SCORES", $scores);
  }
}

sub score_responses_TASK2_DEFAULT {
  my ($self) = @_;
  $self->score_responses_TASK2_STRATEGY1();
}

sub score_responses_TASK2_STRATEGY1 {
  my ($self) = @_;
  my ($logger, $runid, $docid_mappings, $queries, $salient_edges, $responses, $assessments, $queries_to_score)
    = map {$self->get($_)} qw(LOGGER RUNID DOCID_MAPPINGS QUERIES SALIENT_EDGES RESPONSES ASSESSMENTS QUERIES_TO_SCORE);
  my $scores = Task2GraphScoresStrategy1Printer->new($logger);

  # Gather ground truth for Strategy 1A
  # For each single edge query, how many unique (real-world - as determined by LDC's equivalence classes)
  # edges were correct? 
  my %ground_truth;
  foreach my $entry($assessments->toarray()) {
    my ($subject, $predicate, $object, $docid, $correctness, $linkability, $predicate_justification, 
          $object_justification) =
      map {$entry->get($_)}
        qw(SUBJECT_FQEC
           PREDICATE
           OBJECT_FQEC
           DOCUMENT_ID
           PREDICATE_JUSTIFICATION_CORRECTNESS
           OBJECT_LINKABILITY
           PREDICATE_JUSTIFICATION
           OBJECT_JUSTIFICATION);
    $object = join("|", map {"LDC2019E43:".$_} split(/\|/, $object));
    $predicate_justification = join(";", map {"$docid:".$_} split(";", $predicate_justification));
    $object_justification = "$docid:$object_justification";
    my $key = "$predicate:$predicate_justification:$object_justification";
    $logger->NIST_die("Duplicate assessment for key $key") if $ground_truth{"STRATEGY-1A"}{ENTRIES_BY_KEY}{$key};
    $ground_truth{"STRATEGY-1A"}{ENTRIES_BY_KEY}{$key} = $entry;

    next unless ($correctness eq "CORRECT" && $linkability eq "YES");
    my @queries = $queries->get("MATCHING_QUERIES", (PREDICATE=>$predicate, OBJECT=>$object));
    unless (@queries) {
      $logger->record_debug_information("NO_QUERY_FOR_ASSESSNENT_ITEM", $entry->get("LINE"), $entry->get("WHERE"));
      next;
    }
    $entry->set("QUERIES", @queries);
    foreach my $query(@queries) {
      my $query_id = $query->get("QUERYID");
      push(@{$ground_truth{"STRATEGY-1A"}{ENTRIES_BY_SUBJECT}{$query_id}{$subject}}, $entry);
    }
  }

  # Gather ground truth for Strategy 1B
  foreach my $edge($salient_edges->toarray()) {
    my ($subject, $predicate, $object) = map {$edge->get($_)} qw(subject role object);
    $object = join("|", map {"LDC2019E43:".$_} split(/\|/, $object));
    my @queries = $queries->get("MATCHING_QUERIES", (PREDICATE=>$predicate, OBJECT=>$object));
    foreach my $query(@queries) {
      my $query_id = $query->get("QUERYID");
      push(@{$ground_truth{"STRATEGY-1B"}{SALIENT_EDGES}{$query_id}{$subject}}, $edge);
      $self->get("LOGGER")->record_debug_information("SALIENT_FOR_QUERY", "SUBJECT=$subject QUERY=$query_id", $edge->get("WHERE"));
    }
  }

  my %candidate_responses;
  foreach my $response($responses->get("RESPONSES")->toarray()) {
    my ($query_id, $docid, $predicate_justification, $object_justification, $rank) =
      map {$response->get($_)}
        qw(QUERY_ID
           DOCUMENT_ID
           EDGE_PROVENANCE_TRIPLES
           OBJECT_VALUE_PROVENANCE_TRIPLE
           RANK);
    next unless $queries_to_score->exists($query_id);
    next unless $ground_truth{"STRATEGY-1A"}{ENTRIES_BY_SUBJECT}{$query_id};
    my $max_rank = $queries_to_score->get("BY_KEY", $query_id)->get("depth1");
    $response->set("STRATEGY-1A-SUBMITTED", 1) if $rank;
    $response->set("STRATEGY-1A-POOLED", 1) if ($rank && $rank <= $max_rank);
    push(@{$candidate_responses{$query_id}}, $response) if $rank;
  }

  # categorize submissions
  my %categorized_submissions;
  my %correct_found;
  foreach my $query_id(sort keys %candidate_responses) {
    foreach my $response(@{$candidate_responses{$query_id}}) {
      my ($query_id, $docid, $predicate_justification, $object_justification) =
        map {$response->get($_)}
          qw(QUERY_ID
             DOCUMENT_ID
             EDGE_PROVENANCE_TRIPLES
             OBJECT_VALUE_PROVENANCE_TRIPLE);
      my $predicate = $response->get("QUERY")->get("PREDICATE");
      if($response->get("STRATEGY-1A-SUBMITTED")) {
        push(@{$categorized_submissions{"STRATEGY-1A"}{$query_id}{SUBMITTED}}, $response);
        $response->{ASSESSMENT}{"STRATEGY-1A"}{"PRE-POLICY"}{SUBMITTED} = 1;
      }
      if($response->get("STRATEGY-1A-POOLED")) {
        push(@{$categorized_submissions{"STRATEGY-1A"}{$query_id}{POOLED}}, $response);
        $response->{ASSESSMENT}{"STRATEGY-1A"}{"PRE-POLICY"}{POOLED} = 1;
        my $key = "$predicate:$predicate_justification:$object_justification";
        my $assessment = $ground_truth{"STRATEGY-1A"}{ENTRIES_BY_KEY}{$key};
        $logger->NIST_die("Assessment not found for key $key") unless $assessment;
        $response->set("ASSESSMENT_ENTRY", $assessment);
        if($assessment->get("PREDICATE_JUSTIFICATION_CORRECTNESS") eq "CORRECT") {
          push(@{$categorized_submissions{"STRATEGY-1A"}{$query_id}{CORRECT}}, $response);
          $response->{ASSESSMENT}{"STRATEGY-1A"}{"PRE-POLICY"}{CORRECT} = 1;
          if($assessment->get("OBJECT_LINKABILITY") eq "YES") {
            push(@{$categorized_submissions{"STRATEGY-1A"}{$query_id}{PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT}}, $response);
            $response->{ASSESSMENT}{"STRATEGY-1A"}{"PRE-POLICY"}{PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT} = 1;
            my %query_objects = map {$_=>1} split(/\|/, $response->get("QUERY")->get("OBJECT"));
            if($query_objects{"LDC2019E43:".$assessment->get("OBJECT_FQEC")}) {
              # response is either RIGHT or REDUNDANT because it met all the conditions given below:
              #  (1) correct predicate justification,
              #  (2) predicate justification is linkable to object justification, and
              #  (3) object justification is linkable to the query entity
              push(@{$categorized_submissions{"STRATEGY-1A"}{$query_id}{OBJECT_LINKABLE_TO_QUERY_ENTITY}}, $response);
              $response->{ASSESSMENT}{"STRATEGY-1A"}{"PRE-POLICY"}{OBJECT_LINKABLE_TO_QUERY_ENTITY} = 1;
              my $subject = $assessment->get("SUBJECT_FQEC");
              if($correct_found{"STRATEGY-1A"}{$query_id}{$subject}) {
                push(@{$categorized_submissions{"STRATEGY-1A"}{$query_id}{REDUNDANT}}, $response);
                $response->{ASSESSMENT}{"STRATEGY-1A"}{"PRE-POLICY"}{REDUNDANT} = 1;
                push(@{$categorized_submissions{"STRATEGY-1A"}{$query_id}{IGNORE}}, $response);
                $response->{ASSESSMENT}{"STRATEGY-1A"}{"POST-POLICY"}{IGNORE} = 1;
              }
              else{
                push(@{$categorized_submissions{"STRATEGY-1A"}{$query_id}{RIGHT}}, $response);
                $response->{ASSESSMENT}{"STRATEGY-1A"}{"POST-POLICY"}{RIGHT} = 1;
                $correct_found{"STRATEGY-1A"}{$query_id}{$subject} = 1;
                if(exists $ground_truth{"STRATEGY-1B"}{SALIENT_EDGES}{$query_id}{$subject}) {
                  $response->{ASSESSMENT}{"STRATEGY-1B"}{"POST-POLICY"}{SALIENT} = 1;
                  push(@{$categorized_submissions{"STRATEGY-1B"}{$query_id}{SALIENT}}, $response);
                }
              }
            }
            else{
              push(@{$categorized_submissions{"STRATEGY-1A"}{$query_id}{WRONG}}, $response);
              $response->{ASSESSMENT}{"STRATEGY-1A"}{"POST-POLICY"}{WRONG} = 1;
            }
          }
          else {
            push(@{$categorized_submissions{"STRATEGY-1A"}{$query_id}{WRONG}}, $response);
            $response->{ASSESSMENT}{"STRATEGY-1A"}{"POST-POLICY"}{WRONG} = 1;
          }
        }
        elsif($assessment->get("PREDICATE_JUSTIFICATION_CORRECTNESS") eq "INCORRECT") {
          push(@{$categorized_submissions{"STRATEGY-1A"}{$query_id}{INCORRECT}}, $response);
          $response->{ASSESSMENT}{"STRATEGY-1A"}{"PRE-POLICY"}{INCORRECT} = 1;
          push(@{$categorized_submissions{"STRATEGY-1A"}{$query_id}{WRONG}}, $response);
          $response->{ASSESSMENT}{"STRATEGY-1A"}{"POST-POLICY"}{WRONG} = 1;
        }
        else{
          my $filename = $response->get("WHERE")->{FILENAME};
          my $linenum = $response->get("WHERE")->{LINENUM};
          my $line = $response->get("LINE");
          $logger->NIST_die("Unexpected value of assessment found for response\n $line\n in $filename (line#$linenum)\n");
        }
      }
      else {
        $response->{ASSESSMENT}{"STRATEGY-1A"}{"PRE-POLICY"}{NOTPOOLED} = 1;
        $response->{ASSESSMENT}{"STRATEGY-1A"}{"POST-POLICY"}{"NOT-CONSIDERED"} = 1;
      }
      my $pre_policy = join(",", sort keys %{$response->{ASSESSMENT}{"STRATEGY-1A"}{"PRE-POLICY"}});
      my $post_policy = join(",", sort keys %{$response->{ASSESSMENT}{"STRATEGY-1A"}{"POST-POLICY"}});
      my $line = "QUERYID=$query_id " .
                   "DOCID=$docid " .
                   "PREDICATE_JUSTIFICATION=$predicate_justification " .
                   "OBJECT_JUSTIFICATION=$object_justification " .
                   "PRE_POLICY_ASSESSMENT=$pre_policy " .
                   "POST_POLICY_ASSESSMENT=$post_policy\n";
      $logger->record_debug_information("RESPONSE_ASSESSMENT", $line, $response->get("WHERE"));
    }
  }

  foreach my $query_id(sort $queries_to_score->get("ALL_KEYS")) {
    my $num_submitted_1a = @{$categorized_submissions{"STRATEGY-1A"}{$query_id}{SUBMITTED} || []};
    my $num_correct_1a = @{$categorized_submissions{"STRATEGY-1A"}{$query_id}{"CORRECT"} || []};
    my $num_predicate_justification_linkable_to_object_1a = @{$categorized_submissions{"STRATEGY-1A"}{$query_id}{"PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT"} || []};
    my $num_object_linkable_to_query_entity_1a = @{$categorized_submissions{"STRATEGY-1A"}{$query_id}{"OBJECT_LINKABLE_TO_QUERY_ENTITY"} || []};
    my $num_incorrect_1a = @{$categorized_submissions{"STRATEGY-1A"}{$query_id}{"INCORRECT"} || []};
    my $num_right_1a = @{$categorized_submissions{"STRATEGY-1A"}{$query_id}{"RIGHT"} || []};
    my $num_salient_1b = @{$categorized_submissions{"STRATEGY-1B"}{$query_id}{SALIENT} || []};
    my $num_wrong_1a = @{$categorized_submissions{"STRATEGY-1A"}{$query_id}{"WRONG"} || []};
    my $num_redundant_1a = @{$categorized_submissions{"STRATEGY-1A"}{$query_id}{"REDUNDANT"} || []};
    my $num_ignored_1a = @{$categorized_submissions{"STRATEGY-1A"}{$query_id}{"IGNORE"} || []};
    my $num_pooled_1a = @{$categorized_submissions{"STRATEGY-1A"}{$query_id}{"POOLED"} || []};
    my $num_ground_truth_1a = keys %{$ground_truth{"STRATEGY-1A"}{ENTRIES_BY_SUBJECT}{$query_id}};
    my $num_ground_truth_1b = $num_ground_truth_1a ? keys %{$ground_truth{"STRATEGY-1B"}{SALIENT_EDGES}{$query_id}} : 0;
    my $depth1 = $queries_to_score->get("BY_KEY", $query_id)->get("depth1");
    my $num_ground_truth_1a_counted = $num_ground_truth_1a > $depth1 ? $depth1 : $num_ground_truth_1a;
    my $num_ground_truth_1b_counted = $num_ground_truth_1b > $depth1 ? $depth1 : $num_ground_truth_1b;
    $num_ground_truth_1b_counted = $num_ground_truth_1a ? $num_ground_truth_1b_counted : 0;
    my $score = Task2GraphScoreStrategy1->new($logger,
                                  $runid,
                                  $query_id,
                                  $num_submitted_1a,
                                  $num_correct_1a,
                                  $num_predicate_justification_linkable_to_object_1a,
                                  $num_object_linkable_to_query_entity_1a,
                                  $num_incorrect_1a,
                                  $num_right_1a,
                                  $num_salient_1b,
                                  $num_wrong_1a,
                                  $num_redundant_1a,
                                  $num_pooled_1a,
                                  $num_ignored_1a,
                                  $num_ground_truth_1a,
                                  $num_ground_truth_1b,
                                  $num_ground_truth_1a_counted,
                                  $num_ground_truth_1b_counted);
    $scores->add($score, $query_id);
  }
  $self->set("SCORES", $scores);
}

sub score_responses_TASK2_STRATEGY2 {
  my ($self) = @_;
  my ($logger, $runid, $docid_mappings, $queries, $salient_edges, $responses, $assessments, $queries_to_score)
    = map {$self->get($_)} qw(LOGGER RUNID DOCID_MAPPINGS QUERIES SALIENT_EDGES RESPONSES ASSESSMENTS QUERIES_TO_SCORE);
  my $scores = Task2GraphScoresStrategy2Printer->new($logger);

  # Gather ground truth
  my %ground_truth;
  foreach my $entry($assessments->toarray()) {
    my ($subject, $predicate, $object, $docid, $correctness, $linkability, $predicate_justification,
          $object_justification) =
      map {$entry->get($_)}
        qw(SUBJECT_FQEC
           PREDICATE
           OBJECT_FQEC
           DOCUMENT_ID
           PREDICATE_JUSTIFICATION_CORRECTNESS
           OBJECT_LINKABILITY
           PREDICATE_JUSTIFICATION
           OBJECT_JUSTIFICATION);
    $object = join("|", map {"LDC2019E43:".$_} split(/\|/, $object));
    $predicate_justification = join(";", map {"$docid:".$_} split(";", $predicate_justification));
    $object_justification = "$docid:$object_justification";
    my $key = "$predicate:$predicate_justification:$object_justification";
    $logger->NIST_die("Duplicate assessment for key $key") if $ground_truth{"STRATEGY-2"}{ENTRIES_BY_KEY}{$key};
    $ground_truth{"STRATEGY-2"}{ENTRIES_BY_KEY}{$key} = $entry;

    next unless ($correctness eq "CORRECT" && $linkability eq "YES");
    my @queries = $queries->get("MATCHING_QUERIES", (PREDICATE=>$predicate, OBJECT=>$object));
    unless (@queries) {
      $logger->record_debug_information("NO_QUERY_FOR_ASSESSNENT_ITEM", $entry->get("LINE"), $entry->get("WHERE"));
      next;
    }
    $entry->set("QUERIES", @queries);
    foreach my $query(@queries) {
      my $query_id = $query->get("QUERYID");
      push(@{$ground_truth{"STRATEGY-2"}{ENTRIES_BY_SUBJECT}{$query_id}{$subject}}, $entry);
    }
  }

  my %responses_by_query;
  foreach my $response($responses->get("RESPONSES")->toarray()) {
    my ($query_id, $docid, $predicate_justification, $object_justification, $rank) =
      map {$response->get($_)}
        qw(QUERY_ID
           DOCUMENT_ID
           EDGE_PROVENANCE_TRIPLES
           OBJECT_VALUE_PROVENANCE_TRIPLE
           RANK);
    next unless $queries_to_score->exists($query_id);
    next unless $ground_truth{"STRATEGY-2"}{ENTRIES_BY_SUBJECT}{$query_id};
    if($rank) {
      $response->set("STRATEGY-2-SUBMITTED", 1);
      $response->{ASSESSMENT}{"STRATEGY-2"}{"PRE-POLICY"}{SUBMITTED} = 1;
      my $predicate = $response->get("QUERY")->get("PREDICATE");
      my $key = "$predicate:$predicate_justification:$object_justification";
      my $assessment = $ground_truth{"STRATEGY-2"}{ENTRIES_BY_KEY}{$key};
      my %query_objects = map {$_=>1}
                              split(/\|/, $response->get("QUERY")->get("OBJECT"));
      if($assessment) {
        $response->set("ASSESSMENT_ENTRY", $assessment);
        my ($subject, $object, $correctness, $linkability)
          = map {$response->get("ASSESSMENT_ENTRY")->get($_)}
            qw(SUBJECT_FQEC
                OBJECT_FQEC
                PREDICATE_JUSTIFICATION_CORRECTNESS
                OBJECT_LINKABILITY);
        $response->{ASSESSMENT}{"STRATEGY-2"}{"PRE-POLICY"}{$correctness} = 1;
        $response->{ASSESSMENT}{"STRATEGY-2"}{"PRE-POLICY"}{PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT} = 1 if $linkability eq "YES";
        $response->{ASSESSMENT}{"STRATEGY-2"}{"PRE-POLICY"}{OBJECT_LINKABLE_TO_QUERY_ENTITY} = 1
          if($query_objects{"LDC2019E43:".$object});
      }
      push(@{$responses_by_query{$query_id}}, $response);
    }
  }

  # determine what responses were pooled according to strategy#2
  my %response_by_frame_and_subject_cluster;
  my %subject_importance;
  foreach my $query_id(sort keys %responses_by_query) {
    foreach my $response(@{$responses_by_query{$query_id}}) {
      my ($query_id, $docid, $predicate_justification, $object_justification) =
        map {$response->get($_)}
          qw(QUERY_ID
             DOCUMENT_ID
             EDGE_PROVENANCE_TRIPLES
             OBJECT_VALUE_PROVENANCE_TRIPLE);
      my $predicate = $response->get("QUERY")->get("PREDICATE");
      my $subject_cluster = $response->get("SUBJECT_CLUSTER_ID");
      my $ag_cv = $response->get("AG_CV");
      foreach my $frame_id($self->get("FRAMES")->get("FRAMEIDS_FOR_QUERY", $query_id)) {
        $logger->NIST_die("$query_id already exists for subject cluster $subject_cluster already exists")
          if $response_by_frame_and_subject_cluster{$frame_id}{$subject_cluster}{$query_id};
        $response_by_frame_and_subject_cluster{$frame_id}{$subject_cluster}{$query_id} = $response;
        $subject_importance{$frame_id}{$subject_cluster} += $ag_cv;
      }
    }
  }
  foreach my $frame_id(sort keys %subject_importance) {
    my $K = 0;
    foreach my $query_id($self->get("FRAMES")->get("QUERYIDS_FOR_FRAME", $frame_id)) {
      $K += $self->get("QUERIES_TO_SCORE")->get("BY_KEY", $query_id)->get("depth2");
    }
    my $i = 0;
    foreach my $subject_cluster(sort
                  {$subject_importance{$frame_id}{$b}<=>$subject_importance{$frame_id}{$a} || $a cmp $b}
                    keys %{$subject_importance{$frame_id}}) {
      foreach my $query_id( sort {
                                   $response_by_frame_and_subject_cluster{$frame_id}{$subject_cluster}{$b}->get("AG_CV") <=> $response_by_frame_and_subject_cluster{$frame_id}{$subject_cluster}{$a}->get("AG_CV")
                                   || $a cmp $b
                            }
                            keys %{$response_by_frame_and_subject_cluster{$frame_id}{$subject_cluster}}) {
        my $response = $response_by_frame_and_subject_cluster{$frame_id}{$subject_cluster}{$query_id};
        $response->set("STRATEGY-2-POOLED", 1);
        $response->{ASSESSMENT}{"STRATEGY-2"}{"PRE-POLICY"}{POOLED} = 1;
        my $where_string = $response->get("WHERE")->{FILENAME} . " (line " . $response->get("WHERE")->{FILENAME} . " )";
        $logger->NIST_die("Assessment not found for response in " . $where_string) unless $response->get("ASSESSMENT_ENTRY");
        $i++;
        last if $i == $K;
      }
      last if $i == $K;
    }
  }

  foreach my $response($responses->get("RESPONSES")->toarray()) {
    my ($query_id, $docid, $predicate_justification, $object_justification, $subject_cluster_id, $object_cluster_id, $rank) =
      map {$response->get($_)}
        qw(QUERY_ID
           DOCUMENT_ID
           EDGE_PROVENANCE_TRIPLES
           OBJECT_VALUE_PROVENANCE_TRIPLE
           SUBJECT_CLUSTER_ID
           OBJECT_CLUSTER_ID
           RANK);
    next unless $rank;
    if($response->get("STRATEGY-2-POOLED")) {
      my ($correctness, $linkability)
          = map {$response->get("ASSESSMENT_ENTRY")->get($_)}
            qw(PREDICATE_JUSTIFICATION_CORRECTNESS
                OBJECT_LINKABILITY);
      $response->{ASSESSMENT}{"STRATEGY-2"}{"POST-POLICY"}{RIGHT} = 1
        if($correctness eq "CORRECT" && $linkability eq "YES" && $response->{ASSESSMENT}{"STRATEGY-2"}{"PRE-POLICY"}{OBJECT_LINKABLE_TO_QUERY_ENTITY});
      $response->{ASSESSMENT}{"STRATEGY-2"}{"POST-POLICY"}{WRONG} = 1
        unless($correctness eq "CORRECT" && $linkability eq "YES" && $response->{ASSESSMENT}{"STRATEGY-2"}{"PRE-POLICY"}{OBJECT_LINKABLE_TO_QUERY_ENTITY});
    }
    else {
      $response->{ASSESSMENT}{"STRATEGY-2"}{"PRE-POLICY"}{NOTPOOLED} = 1;
      $response->{ASSESSMENT}{"STRATEGY-2"}{"POST-POLICY"}{"NOT-CONSIDERED"} = 1;
    }
    my $pre_policy = join(",", sort keys %{$response->{ASSESSMENT}{"STRATEGY-2"}{"PRE-POLICY"}});
    my $post_policy = join(",", sort keys %{$response->{ASSESSMENT}{"STRATEGY-2"}{"POST-POLICY"}});
    my $line = "QUERYID=$query_id " .
                   "DOCID=$docid " .
                   "PREDICATE_JUSTIFICATION=$predicate_justification " .
                   "OBJECT_JUSTIFICATION=$object_justification " .
                   "SUBJECT_CLUSTER_ID=$subject_cluster_id " .
                   "OBJECT_CLUSTER_ID=$object_cluster_id " .
                   "PRE_POLICY_ASSESSMENT=$pre_policy " .
                   "POST_POLICY_ASSESSMENT=$post_policy\n";
    $logger->record_debug_information("RESPONSE_ASSESSMENT", $line, $response->get("WHERE"));
  }

  # For each query frame, compute the Value for each subject event/relation KE (i.e subject cluster)
  # that was submitted and pooled for the query frame; the Value is the maximum number of unique edges
  # in the submitted event/relation KE that are correct and that have the same global KB ID for the subject.
  foreach my $frame_id(sort $self->get("FRAMES")->get("ALL_KEYS")) {
    foreach my $query_id($self->get("FRAMES")->get("QUERYIDS_FOR_FRAME", $frame_id)) {
      my $line = "FRAMEID=$frame_id QUERYID=$query_id\n";
      $logger->record_debug_information("FRAME_QUERY", $line, "NO_SOURCE");
    }
    my %cluster_value;
    foreach my $subject_cluster(keys %{$response_by_frame_and_subject_cluster{$frame_id}}) {
      # each query has a single response
      # each query-response pair defines a unique edge
      my %correct_edges;
      foreach my $query_id(sort keys %{$response_by_frame_and_subject_cluster{$frame_id}{$subject_cluster}}) {
        my $response = $response_by_frame_and_subject_cluster{$frame_id}{$subject_cluster}{$query_id};
        my ($docid, $predicate_justification, $object_justification, $rank) =
          map {$response->get($_)}
            qw(DOCUMENT_ID
            EDGE_PROVENANCE_TRIPLES
            OBJECT_VALUE_PROVENANCE_TRIPLE
            RANK);
        next unless $response->get("STRATEGY-2-POOLED");
        my ($subject, $predicate, $object, $correctness, $linkability)
          = map {$response->get("ASSESSMENT_ENTRY")->get($_)}
            qw(SUBJECT_FQEC
                PREDICATE
                OBJECT_FQEC
                PREDICATE_JUSTIFICATION_CORRECTNESS
                OBJECT_LINKABILITY);
        my %query_objects = map {$_=>1}
                              split(/\|/, $response->get("QUERY")->get("OBJECT"));
        if($correctness eq "CORRECT" && $linkability eq "YES" && $query_objects{"LDC2019E43:".$object}) {
          $logger->NIST_die("duplicate edge $subject:$predicate:$object found in response to FRAME_ID=$frame_id SUBJECT_CLUSTER=$subject_cluster and QUERY=$query_id")
            if($correct_edges{"$subject:$predicate:$object"});
          $correct_edges{"$subject:$predicate:$object"} = 1;
          my $line = "FRAMEID=$frame_id " .
                         "QUERYID=$query_id " .
                         "DOCID=$docid " .
                         "SUBJECT_CLUSTER=$subject_cluster " .
                         "PREDICATE_JUSTIFICATION=$predicate_justification " .
                         "OBJECT_JUSTIFICATION=$object_justification " .
                         "RANK=$rank " .
                         "SUBJECT_FQEC=$subject " .
                         "PREDICATE=$predicate " .
                         "OBJECT_FQEC=$object";
          $logger->record_debug_information("CORRECT_EDGE", $line, $response->get("WHERE"));
        }
      }
      $cluster_value{$subject_cluster} = scalar keys %correct_edges;
    }
    my ($best_subject_cluster) = sort {$cluster_value{$b}<=>$cluster_value{$a}} keys %cluster_value;
    my $frame_value = 0;
    $frame_value = $cluster_value{$best_subject_cluster}
      if $best_subject_cluster && exists $cluster_value{$best_subject_cluster};
    my $num_queries_in_frame = scalar $self->get("FRAMES")->get("QUERYIDS_FOR_FRAME", $frame_id);
    my $frame_recall = $frame_value/$num_queries_in_frame;

    my $score = Task2GraphScoreStrategy2->new($logger,
                                  $runid,
                                  $frame_id,
                                  $num_queries_in_frame,
                                  $frame_value,
                                  $frame_recall);
    $scores->add($score, $frame_id);
  }
  $self->set("SCORES", $scores);
}

sub print_lines {
  my ($self, $program_output) = @_;
  $self->get("SCORES")->print_lines($program_output);
}

#####################################################################################
# Task1GraphScoresStrategy1Printer
#####################################################################################

package Task1GraphScoresStrategy1Printer;

use parent -norequire, 'Container', 'Super';

my @task1_graph_scorer_strategy1_fields_to_print = (
  {NAME => 'EC',                                             HEADER => 'QID/EC',         FORMAT => '%s',     JUSTIFY => 'L'},
  {NAME => 'DOCUMENT_ID',                                    HEADER => 'DocID',          FORMAT => '%s',     JUSTIFY => 'L'},
  {NAME => 'RUNID',                                          HEADER => 'RunID',          FORMAT => '%s',     JUSTIFY => 'L'},
  {NAME => 'NUM_GROUND_TRUTH_1A',                            HEADER => 'GTA',            FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_GROUND_TRUTH_1A_COUNTED',                    HEADER => 'GT',             FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_SUBMITTED_1A',                               HEADER => 'Sub',            FORMAT => '%4d',    JUSTIFY => 'R'},
  {NAME => 'NUM_POOLED_1A',                                  HEADER => 'Pooled',         FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_CORRECT_1A',                                 HEADER => 'Correct',        FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT', HEADER => 'PJLnkabl2O',     FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_REDUNDANT_1A',                               HEADER => 'Dup',            FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_INCORRECT_1A',                               HEADER => 'Incrct',         FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_COUNTED_1A',                                 HEADER => 'Cntd',           FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_RIGHT_1A',                                   HEADER => 'Right',          FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_WRONG_1A',                                   HEADER => 'Wrong',          FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_IGNORED_1A',                                 HEADER => 'Ignrd',          FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'PRECISION_1A',                                   HEADER => 'Prec',           FORMAT => '%6.4f',  JUSTIFY => 'L'},
  {NAME => 'RECALL_1A',                                      HEADER => 'Recall',         FORMAT => '%6.4f',  JUSTIFY => 'L'},
  {NAME => 'F1_1A',                                          HEADER => 'F1',             FORMAT => '%6.4f',  JUSTIFY => 'L'},
);

sub new {
  my ($class, $logger, $program_output) = @_;
  my $self = $class->SUPER::new($logger, 'Score');
  $self->{__CLASS__} = 'Task1GraphScoresStrategy1Printer';
  $self->{PROGRAM_OUTPUT} = $program_output;
  $self->{WIDTHS} = {map {$_->{NAME} => length($_->{HEADER})} @task1_graph_scorer_strategy1_fields_to_print};
  $self->{LOGGER} = $logger;
  $self->{LINES} = [];
  @{$self->{FIELDS_TO_PRINT}} = @task1_graph_scorer_strategy1_fields_to_print;
  bless($self, $class);
  $self;
}

sub get_SUMMARY {
  my ($self) = @_;
  my $logger = $self->get("LOGGER");
  my ($runid, 
      $total_num_submitted_1a, 
      $total_num_correct_1a, 
      $total_num_predicate_justification_linkable_to_object_1a,
      $total_num_incorrect_1a, 
      $total_num_right_1a,
      $total_num_wrong_1a, 
      $total_num_redundant_1a, 
      $total_num_pooled_1a, 
      $total_num_ignored_1a, 
      $total_num_ground_truth_1a,
      $total_num_ground_truth_1a_counted);
  foreach my $score($self->toarray()) {
    my ($num_submitted_1a,
        $num_correct_1a,
        $num_predicate_justification_linkable_to_object_1a,
        $num_incorrect_1a,
        $num_right_1a,
        $num_wrong_1a,
        $num_redundant_1a,
        $num_pooled_1a,
        $num_ignored_1a,
        $num_ground_truth_1a,
        $num_ground_truth_1a_counted)
      = map {$score->get($_)} qw(
                                  NUM_SUBMITTED_1A
                                  NUM_CORRECT_1A
                                  NUM_PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT
                                  NUM_INCORRECT_1A
                                  NUM_RIGHT_1A
                                  NUM_WRONG_1A
                                  NUM_REDUNDANT_1A
                                  NUM_POOLED_1A
                                  NUM_IGNORED_1A
                                  NUM_GROUND_TRUTH_1A
                                  NUM_GROUND_TRUTH_1A_COUNTED
                              );
    $runid = $score->get("RUNID") unless $runid;
    $total_num_submitted_1a += $num_submitted_1a;
    $total_num_correct_1a += $num_correct_1a;
    $total_num_predicate_justification_linkable_to_object_1a += $num_predicate_justification_linkable_to_object_1a;
    $total_num_incorrect_1a += $num_incorrect_1a;
    $total_num_right_1a += $num_right_1a;
    $total_num_wrong_1a += $num_wrong_1a;
    $total_num_redundant_1a += $num_redundant_1a;
    $total_num_pooled_1a += $num_pooled_1a;
    $total_num_ignored_1a += $num_ignored_1a;
    $total_num_ground_truth_1a += $num_ground_truth_1a;
    $total_num_ground_truth_1a_counted += $num_ground_truth_1a_counted;
  }

  Task1GraphScoreStrategy1->new($logger,
                    $runid, 
                    "Summary",
                    "",
                    $total_num_submitted_1a,
                    $total_num_correct_1a,
                    $total_num_predicate_justification_linkable_to_object_1a,
                    $total_num_incorrect_1a,
                    $total_num_right_1a,
                    $total_num_wrong_1a,
                    $total_num_redundant_1a,
                    $total_num_pooled_1a,
                    $total_num_ignored_1a,
                    $total_num_ground_truth_1a,
                    $total_num_ground_truth_1a_counted);
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
  push(@scores, $self->get("SUMMARY"));
  foreach my $score (@scores) {
    my %elements_to_print;
    foreach my $field (@{$self->{FIELDS_TO_PRINT}}) {
      my $value = $score->get($field->{NAME});
      my $field_name = $field->{NAME};
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
# Task1GraphScoreStrategy1
#####################################################################################

package Task1GraphScoreStrategy1;

use parent -norequire, 'Super';

sub new {
  my ($class, 
      $logger,
      $runid,
      $query_id,
      $docid,
      $num_submitted_1a,
      $num_correct_1a,
      $num_predicate_justification_linkable_to_object_1a,
      $num_incorrect_1a,
      $num_right_1a,
      $num_wrong_1a,
      $num_redundant_1a,
      $num_pooled_1a,
      $num_ignored_1a,
      $num_ground_truth_1a,
      $num_ground_truth_1a_counted) = @_;

  my $self = {
    __CLASS__ => 'Task1GraphScoreStrategy1',
    EC => $query_id,
    DOCUMENT_ID => $docid,
    NUM_CORRECT_1A => $num_correct_1a,
    NUM_PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT => $num_predicate_justification_linkable_to_object_1a,
    NUM_GROUND_TRUTH_1A => $num_ground_truth_1a,
    NUM_GROUND_TRUTH_1A_COUNTED => $num_ground_truth_1a_counted,
    NUM_IGNORED_1A => $num_ignored_1a,
    NUM_INCORRECT_1A => $num_incorrect_1a,
    NUM_POOLED_1A => $num_pooled_1a,
    NUM_REDUNDANT_1A => $num_redundant_1a,
    NUM_RIGHT_1A => $num_right_1a,
    NUM_SUBMITTED_1A => $num_submitted_1a,
    NUM_WRONG_1A => $num_wrong_1a,
    RUNID => $runid,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub get_NUM_COUNTED_1A {
  my ($self) = @_;
  $self->get("NUM_RIGHT_1A") + $self->get("NUM_WRONG_1A");
}

sub get_PRECISION_1A {
  my ($self) = @_;
  $self->get("NUM_COUNTED_1A") ? $self->get("NUM_RIGHT_1A")/($self->get("NUM_COUNTED_1A")) : 0;
}

sub get_RECALL_1A {
  my ($self) = @_;
  $self->get("NUM_GROUND_TRUTH_1A") ? $self->get("NUM_RIGHT_1A")/($self->get("NUM_GROUND_TRUTH_1A_COUNTED")) : 0;
}

sub get_F1_1A {
  my ($self) = @_;
  my $precision = $self->get("PRECISION_1A");
  my $recall = $self->get("RECALL_1A");
  ($precision + $recall) ? 2*$precision*$recall/($precision + $recall) : 0;
}

#####################################################################################
# Task2GraphScoresStrategy1Printer
#####################################################################################

package Task2GraphScoresStrategy1Printer;

use parent -norequire, 'Container', 'Super';

my @task2_graph_scorer_strategy1_fields_to_print = (
  {NAME => 'EC',                                             HEADER => 'QID/EC',         FORMAT => '%s',     JUSTIFY => 'L'},
  {NAME => 'RUNID',                                          HEADER => 'RunID',          FORMAT => '%s',     JUSTIFY => 'L'},
  {NAME => 'NUM_GROUND_TRUTH_1A',                            HEADER => 'GTA(1a)',        FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_GROUND_TRUTH_1A_COUNTED',                    HEADER => 'GT(1a)',         FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_GROUND_TRUTH_1B',                            HEADER => 'GTA(1b)',        FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_GROUND_TRUTH_1B_COUNTED',                    HEADER => 'GT(1b)',         FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_SUBMITTED_1A',                               HEADER => 'Sub',            FORMAT => '%4d',    JUSTIFY => 'R'},
  {NAME => 'NUM_POOLED_1A',                                  HEADER => 'Pooled',         FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_CORRECT_1A',                                 HEADER => 'Correct',        FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT', HEADER => 'PJLnkabl2O',     FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_OBJECT_LINKABLE_TO_QUERY_ENTITY_1A',         HEADER => 'OLnkabl2QE',     FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_REDUNDANT_1A',                               HEADER => 'Dup',            FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_INCORRECT_1A',                               HEADER => 'Incrct',         FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_COUNTED_1A',                                 HEADER => 'Cntd',           FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_RIGHT_1A',                                   HEADER => 'Right',          FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_WRONG_1A',                                   HEADER => 'Wrong',          FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_IGNORED_1A',                                 HEADER => 'Ignrd',          FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'NUM_SALIENT_1B',                                 HEADER => 'Salient',        FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'PRECISION_1A',                                   HEADER => 'Prec(1a)',       FORMAT => '%6.4f',  JUSTIFY => 'L'},
  {NAME => 'RECALL_1A',                                      HEADER => 'Recall(1a)',     FORMAT => '%6.4f',  JUSTIFY => 'L'},
  {NAME => 'F1_1A',                                          HEADER => 'F1(1a)',         FORMAT => '%6.4f',  JUSTIFY => 'L'},
  {NAME => 'RECALL_1B',                                      HEADER => 'Recall(1b)',     FORMAT => '%6.4f',  JUSTIFY => 'L'},
);

sub new {
  my ($class, $logger, $program_output) = @_;
  my $self = $class->SUPER::new($logger, 'Score');
  $self->{__CLASS__} = 'Task2GraphScoresStrategy1Printer';
  $self->{PROGRAM_OUTPUT} = $program_output;
  $self->{WIDTHS} = {map {$_->{NAME} => length($_->{HEADER})} @task2_graph_scorer_strategy1_fields_to_print};
  $self->{LOGGER} = $logger;
  $self->{LINES} = [];
  @{$self->{FIELDS_TO_PRINT}} = @task2_graph_scorer_strategy1_fields_to_print;
  bless($self, $class);
  $self;
}

sub get_SUMMARY {
  my ($self) = @_;
  my $logger = $self->get("LOGGER");
  my ($runid, 
      $total_num_submitted_1a, 
      $total_num_correct_1a, 
      $total_num_predicate_justification_linkable_to_object_1a,
      $total_num_object_linkable_to_query_entity_1a,
      $total_num_incorrect_1a, 
      $total_num_right_1a,
      $total_num_salient_1b,
      $total_num_wrong_1a, 
      $total_num_redundant_1a, 
      $total_num_pooled_1a, 
      $total_num_ignored_1a, 
      $total_num_ground_truth_1a,
      $total_num_ground_truth_1b,
      $total_num_ground_truth_1a_counted,
      $total_num_ground_truth_1b_counted);
  foreach my $score($self->toarray()) {
    my ($num_submitted_1a,
        $num_correct_1a,
        $num_predicate_justification_linkable_to_object_1a,
        $num_object_linkable_to_query_entity_1a,
        $num_incorrect_1a,
        $num_right_1a,
        $num_salient_1b,
        $num_wrong_1a,
        $num_redundant_1a,
        $num_pooled_1a,
        $num_ignored_1a,
        $num_ground_truth_1a,
        $num_ground_truth_1b,
        $num_ground_truth_1a_counted,
        $num_ground_truth_1b_counted)
      = map {$score->get($_)} qw(
                                  NUM_SUBMITTED_1A
                                  NUM_CORRECT_1A
                                  NUM_PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT
                                  NUM_OBJECT_LINKABLE_TO_QUERY_ENTITY_1A
                                  NUM_INCORRECT_1A
                                  NUM_RIGHT_1A
                                  NUM_SALIENT_1B
                                  NUM_WRONG_1A
                                  NUM_REDUNDANT_1A
                                  NUM_POOLED_1A
                                  NUM_IGNORED_1A
                                  NUM_GROUND_TRUTH_1A
                                  NUM_GROUND_TRUTH_1B
                                  NUM_GROUND_TRUTH_1A_COUNTED
                                  NUM_GROUND_TRUTH_1B_COUNTED
                              );
    $runid = $score->get("RUNID") unless $runid;
    $total_num_submitted_1a += $num_submitted_1a;
    $total_num_correct_1a += $num_correct_1a;
    $total_num_predicate_justification_linkable_to_object_1a += $num_predicate_justification_linkable_to_object_1a;
    $total_num_object_linkable_to_query_entity_1a += $num_object_linkable_to_query_entity_1a;
    $total_num_incorrect_1a += $num_incorrect_1a;
    $total_num_right_1a += $num_right_1a;
    $total_num_salient_1b += $num_salient_1b;
    $total_num_wrong_1a += $num_wrong_1a;
    $total_num_redundant_1a += $num_redundant_1a;
    $total_num_pooled_1a += $num_pooled_1a;
    $total_num_ignored_1a += $num_ignored_1a;
    $total_num_ground_truth_1a += $num_ground_truth_1a;
    $total_num_ground_truth_1b += $num_ground_truth_1b;
    $total_num_ground_truth_1a_counted += $num_ground_truth_1a_counted;
    $total_num_ground_truth_1b_counted += $num_ground_truth_1b_counted;
  }

  Task2GraphScoreStrategy1->new($logger,
                    $runid, 
                    "Summary", 
                    $total_num_submitted_1a,
                    $total_num_correct_1a,
                    $total_num_predicate_justification_linkable_to_object_1a,
                    $total_num_object_linkable_to_query_entity_1a,
                    $total_num_incorrect_1a,
                    $total_num_right_1a,
                    $total_num_salient_1b,
                    $total_num_wrong_1a,
                    $total_num_redundant_1a,
                    $total_num_pooled_1a,
                    $total_num_ignored_1a,
                    $total_num_ground_truth_1a,
                    $total_num_ground_truth_1b,
                    $total_num_ground_truth_1a_counted,
                    $total_num_ground_truth_1b_counted);
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
  push(@scores, $self->get("SUMMARY"));
  foreach my $score (@scores) {
    my %elements_to_print;
    foreach my $field (@{$self->{FIELDS_TO_PRINT}}) {
      my $value = $score->get($field->{NAME});
      my $field_name = $field->{NAME};
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
# Task2GraphScoreStrategy1
#####################################################################################

package Task2GraphScoreStrategy1;

use parent -norequire, 'Super';

sub new {
  my ($class, 
      $logger,
      $runid,
      $query_id,
      $num_submitted_1a,
      $num_correct_1a,
      $num_predicate_justification_linkable_to_object_1a,
      $num_object_linkable_to_query_entity_1a,
      $num_incorrect_1a,
      $num_right_1a,
      $num_salient_1b,
      $num_wrong_1a,
      $num_redundant_1a,
      $num_pooled_1a,
      $num_ignored_1a,
      $num_ground_truth_1a,
      $num_ground_truth_1b,
      $num_ground_truth_1a_counted,
      $num_ground_truth_1b_counted) = @_;
      
  my $self = {
    __CLASS__ => 'Task2GraphScoreStrategy1',
    EC => $query_id,
    NUM_CORRECT_1A => $num_correct_1a,
    NUM_PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT => $num_predicate_justification_linkable_to_object_1a,
    NUM_GROUND_TRUTH_1A => $num_ground_truth_1a,
    NUM_GROUND_TRUTH_1A_COUNTED => $num_ground_truth_1a_counted,
    NUM_GROUND_TRUTH_1B => $num_ground_truth_1b,
    NUM_GROUND_TRUTH_1B_COUNTED => $num_ground_truth_1b_counted,
    NUM_IGNORED_1A => $num_ignored_1a,
    NUM_INCORRECT_1A => $num_incorrect_1a,
    NUM_OBJECT_LINKABLE_TO_QUERY_ENTITY_1A => $num_object_linkable_to_query_entity_1a,
    NUM_POOLED_1A => $num_pooled_1a,
    NUM_REDUNDANT_1A => $num_redundant_1a,
    NUM_RIGHT_1A => $num_right_1a,
    NUM_SALIENT_1B => $num_salient_1b,
    NUM_SUBMITTED_1A => $num_submitted_1a,
    NUM_WRONG_1A => $num_wrong_1a,
    RUNID => $runid,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub get_NUM_COUNTED_1A {
  my ($self) = @_;
  $self->get("NUM_RIGHT_1A") + $self->get("NUM_WRONG_1A");
}

sub get_PRECISION_1A {
  my ($self) = @_;
  $self->get("NUM_COUNTED_1A") ? $self->get("NUM_RIGHT_1A")/($self->get("NUM_COUNTED_1A")) : 0;
}

sub get_RECALL_1A {
  my ($self) = @_;
  $self->get("NUM_GROUND_TRUTH_1A") ? $self->get("NUM_RIGHT_1A")/($self->get("NUM_GROUND_TRUTH_1A_COUNTED")) : 0;
}

sub get_RECALL_1B {
  my ($self) = @_;
  $self->get("NUM_GROUND_TRUTH_1B") ? $self->get("NUM_SALIENT_1B")/($self->get("NUM_GROUND_TRUTH_1B_COUNTED")) : 0;
}

sub get_F1_1A {
  my ($self) = @_;
  my $precision = $self->get("PRECISION_1A");
  my $recall = $self->get("RECALL_1A");
  ($precision + $recall) ? 2*$precision*$recall/($precision + $recall) : 0;
}

#####################################################################################
# Task2GraphScoresStrategy2Printer
#####################################################################################

package Task2GraphScoresStrategy2Printer;

use parent -norequire, 'Container', 'Super';

my @task2_graph_scorer_strategy2_fields_to_print = (
  {NAME => 'EC',                            HEADER => 'FrameID',        FORMAT => '%s',     JUSTIFY => 'L'},
  {NAME => 'RUNID',                         HEADER => 'RunID',          FORMAT => '%s',     JUSTIFY => 'L'},
  {NAME => 'NUM_QUERIES_IN_FRAME',          HEADER => 'NumQueries',     FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'FRAME_VALUE',                   HEADER => 'FrameValue',     FORMAT => '%4d',    JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
  {NAME => 'FRAME_RECALL',                  HEADER => 'FrameRecall',    FORMAT => '%6.4f',  JUSTIFY => 'R', MEAN_FORMAT => '%4.2f'},
);

sub new {
  my ($class, $logger, $program_output) = @_;
  my $self = $class->SUPER::new($logger, 'Score');
  $self->{__CLASS__} = 'Task2GraphScoresStrategy2Printer';
  $self->{PROGRAM_OUTPUT} = $program_output;
  $self->{WIDTHS} = {map {$_->{NAME} => length($_->{HEADER})} @task2_graph_scorer_strategy2_fields_to_print};
  $self->{LOGGER} = $logger;
  $self->{LINES} = [];
  @{$self->{FIELDS_TO_PRINT}} = @task2_graph_scorer_strategy2_fields_to_print;
  bless($self, $class);
  $self;
}

sub get_SUMMARY {
  my ($self) = @_;
  my $logger = $self->get("LOGGER");
  my ($runid,
      $total_num_queries_in_frame,
      $total_frame_value,
      $total_frame_recall);
  my $num_frames = 0;
  foreach my $score($self->toarray()) {
    $num_frames++;
    my ($num_queries_in_frame,
        $frame_value,
        $frame_recall)
      = map {$score->get($_)} qw(
                                  NUM_QUERIES_IN_FRAME
                                  FRAME_VALUE
                                  FRAME_RECALL
                              );
    $runid = $score->get("RUNID") unless $runid;
    $total_num_queries_in_frame += $num_queries_in_frame;
    $total_frame_value += $frame_value;
    $total_frame_recall += $frame_recall;
  }

  my $mean_frame_recall = $total_frame_recall / $num_frames;

  Task2GraphScoreStrategy2->new($logger,
                                  $runid,
                                  "Summary",
                                  $total_num_queries_in_frame,
                                  $total_frame_value,
                                  $mean_frame_recall);
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
  push(@scores, $self->get("SUMMARY"));
  foreach my $score (@scores) {
    my %elements_to_print;
    foreach my $field (@{$self->{FIELDS_TO_PRINT}}) {
      my $value = $score->get($field->{NAME});
      my $field_name = $field->{NAME};
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
# Task2GraphScoreStrategy2
#####################################################################################

package Task2GraphScoreStrategy2;
use parent -norequire, 'Super';
sub new {
  my ($class,
      $logger,
      $runid,
      $frame_id,
      $num_queries_in_frame,
      $frame_value,
      $frame_recall) = @_;

  my $self = {
    __CLASS__ => 'Task2GraphScoreStrategy2',
    EC => $frame_id,
    FRAME_VALUE => $frame_value,
    FRAME_RECALL => $frame_recall,
    NUM_QUERIES_IN_FRAME => $num_queries_in_frame,
    RUNID => $runid,
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
    __CLASS__ => 'EncodingFormatToModalityMappings',
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

#####################################################################################
# ImagesBoundingBoxes
#####################################################################################

package ImagesBoundingBoxes;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $filename) = @_;
  my $self = $class->SUPER::new($logger, 'ImageBoundingBox');
  $self->{__CLASS__} = 'ImagesBoundingBoxes';
  $self->{FILENAME} = $filename;
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self->load();
  $self;
}

sub load {
  my ($self) = @_;
  my $filehandler = FileHandler->new($self->get("LOGGER"), $self->get("FILENAME"));
  my $entries = $filehandler->get("ENTRIES");
  foreach my $entry( $entries->toarray() ){
    my $filename = $entry->get("filename");
    my $doceid = $filename;
    $doceid =~ s/\..*?$//;
    my ($bottom_right_x, $bottom_right_y) = (0,0);
    ($bottom_right_x, $bottom_right_y) = split(/x/, $entry->get("wxh")) if $entry->get("wxh");
    $self->add(ImageBoundingBox->new($self->get("LOGGER"), $doceid, undef,
                        0, 0, $bottom_right_x, $bottom_right_y), $doceid);
  }
}

#####################################################################################
# ImageBoundingBox
#####################################################################################

package ImageBoundingBox;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $doceid, $type, $top_left_x, $top_left_y, $bottom_right_x, $bottom_right_y) = @_;
  my $self = {
    __CLASS__ => 'ImageBoundingBox',
    DOCEID => $doceid,
    TYPE => $type,
    TOP_LEFT_X => $top_left_x,
    TOP_LEFT_Y => $top_left_y,
    BOTTOM_RIGHT_X => $bottom_right_x,
    BOTTOM_RIGHT_Y => $bottom_right_y,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub get_START {
  my ($self) = @_;
  $self->get("TOP_LEFT_X") . "," . $self->get("TOP_LEFT_Y");
}

sub get_END {
  my ($self) = @_;
  $self->get("BOTTOM_RIGHT_X") . "," . $self->get("BOTTOM_RIGHT_Y");
}

sub validate {
  my ($self, $span_string) = @_;
  my $is_valid = 0;
  if(my ($id, $eid, $sx, $sy, $ex, $ey) = $span_string =~ /^(.*?):(.*?):\((\d+)\,(\d+)\)-\((\d+)\,(\d+)\)$/) {
    my ($min_x, $min_y, $max_x, $max_y) 
      = map {$self->get($_)} 
        qw(TOP_LEFT_X TOP_LEFT_Y BOTTOM_RIGHT_X BOTTOM_RIGHT_Y);
    $is_valid = 1
      unless($sx < $min_x || $sx > $max_x || $ex < $min_x || $ex > $max_x
        || $sy < $min_y || $sy > $max_y || $ey < $min_y || $ey > $max_y);
  }
  $is_valid;
}

sub tostring {
  my ($self) = @_;
  "(" . $self->get("START") . ")-(" . $self->get("END") . ")";
}

#####################################################################################
# KeyFramesBoundingBoxes
#####################################################################################

package KeyFramesBoundingBoxes;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $filename) = @_;
  my $self = $class->SUPER::new($logger, 'KeyFrameBoundingBox');
  $self->{__CLASS__} = 'KeyFramesBoundingBoxes';
  $self->{FILENAME} = $filename;
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self->load();
  $self;
}

sub load {
  my ($self) = @_;
  my $filehandler = FileHandler->new($self->get("LOGGER"), $self->get("FILENAME"));
  my $entries = $filehandler->get("ENTRIES");
  foreach my $entry( $entries->toarray() ){
    my ($bottom_right_x, $bottom_right_y) = (0,0);
    ($bottom_right_x, $bottom_right_y) = split(/x/, $entry->get("wxh")) if $entry->get("wxh");
    $self->add(KeyFrameBoundingBox->new($self->get("LOGGER"), $entry->get("keyframeid"),
                        0, 0,
                        $bottom_right_x, $bottom_right_y),
                $entry->get("keyframeid"));
  }
}

sub get_KEYFRAMESIDS {
  my ($self, $doceid) = @_;
  my @keyframeids = $self->get("ALL_KEYS");
  @keyframeids = grep {$_ =~ /^$doceid/} @keyframeids if $doceid;
  sort @keyframeids;
}

#####################################################################################
# KeyFramesBoundingBox
#####################################################################################

package KeyFrameBoundingBox;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $keyframeid, $top_left_x, $top_left_y, $bottom_right_x, $bottom_right_y) = @_;
  my $self = {
    __CLASS__ => 'KeyFrameBoundingBox',
    KEYFRAMEID => $keyframeid,
    TOP_LEFT_X => $top_left_x,
    TOP_LEFT_Y => $top_left_y,
    BOTTOM_RIGHT_X => $bottom_right_x,
    BOTTOM_RIGHT_Y => $bottom_right_y,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub get_DOCEID {
  my ($self) = @_;
  my ($doceid) = split("_", $self->get("KEYFRAMEID"));
  $doceid;
}

sub get_START {
  my ($self) = @_;
  $self->get("TOP_LEFT_X") . "," . $self->get("TOP_LEFT_Y");
}

sub get_END {
  my ($self) = @_;
  $self->get("BOTTOM_RIGHT_X") . "," . $self->get("BOTTOM_RIGHT_Y");
}

sub validate {
  my ($self, $span_string) = @_;
  my $is_valid = 0;
  if(my ($id, $eid, $sx, $sy, $ex, $ey) = $span_string =~ /^(.*?):(.*?):\((\d+)\,(\d+)\)-\((\d+)\,(\d+)\)$/) {
    my ($min_x, $min_y, $max_x, $max_y) 
      = map {$self->get($_)} 
        qw(TOP_LEFT_X TOP_LEFT_Y BOTTOM_RIGHT_X BOTTOM_RIGHT_Y);
    $is_valid = 1
      unless($sx < $min_x || $sx > $max_x || $ex < $min_x || $ex > $max_x
        || $sy < $min_y || $sy > $max_y || $ey < $min_y || $ey > $max_y);
  }
  $is_valid;
}

sub tostring {
  my ($self) = @_;
  "(" . $self->get("START") . ")-(" . $self->get("END") . ")";
}

#####################################################################################
# TextDocumentBoundaries
#####################################################################################

package TextDocumentBoundaries;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $filename) = @_;
  my $self = $class->SUPER::new($logger, 'TextDocumentBoundary');
  $self->{__CLASS__} = 'TextDocumentBoundaries';
  $self->{FILENAME} = $filename;
  $self->{LOGGER} = $logger;
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
    my ($doceid, $segment_id, $start_char, $end_char) =
      map {$entry->get($_)} qw(doceid segment_id start_char end_char);
    my $text_document_boundary;
    unless($self->exists($doceid)) {
      $text_document_boundary = $self->get("BY_KEY", $doceid);
      $text_document_boundary->set("DOCEID", $doceid);
      $text_document_boundary->set("START_CHAR", $start_char);
      $text_document_boundary->set("END_CHAR", $end_char);
    }
    else{
      $text_document_boundary = $self->get("BY_KEY", $doceid);
    }
    my ($tb_start_char, $tb_end_char)
      = map {$text_document_boundary->get($_)}
        qw(START_CHAR END_CHAR);
    $text_document_boundary->set("START_CHAR", $start_char)
      if($start_char < $tb_start_char);
    $text_document_boundary->set("END_CHAR", $end_char)
      if($end_char > $tb_end_char);
  }
}

sub get_BOUNDARY {
  my ($self, $span_string) = @_;
  my ($id, $sx, $sy, $ex, $ey) = $span_string =~ /^(.*?):\((\d+)\,(\d+)\)-\((\d+)\,(\d+)\)$/;
  my $text_document_boundary;
  $text_document_boundary = $self->get("BY_KEY", $id) 
    if($self->exists($id));
  $text_document_boundary;
}

#####################################################################################
# TextDocumentBoundary
#####################################################################################

package TextDocumentBoundary;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $start_char, $end_char) = @_;
  my $self = {
    __CLASS__ => 'TextDocumentBoundary',
    START_CHAR => $start_char,
    END_CHAR => $end_char,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub get_START {
  my ($self) = @_;
  $self->get("START_CHAR") . ",0";
}

sub get_END {
  my ($self) = @_;
  $self->get("END_CHAR") . ",0";
}

sub validate {
  my ($self, $span_string) = @_;
  my $is_valid = 0;
  if(my ($id, $eid, $sx, $sy, $ex, $ey) = $span_string =~ /^(.*?):(.*?):\((\d+)\,(\d+)\)-\((\d+)\,(\d+)\)$/) {
    my ($min_y, $max_y) = (0,0);
    my ($min_x, $max_x) 
      = map {$self->get($_)} 
        qw(START_CHAR END_CHAR);
    $is_valid = 1
      unless($sx < $min_x || $sx > $max_x || $ex < $min_x || $ex > $max_x
        || $sy < $min_y || $sy > $max_y || $ey < $min_y || $ey > $max_y);
  }
  $is_valid;
}

sub tostring {
  my ($self) = @_;
  "(" . $self->get("START") . ")-(" . $self->get("END") . ")";
}


#####################################################################################
# SentenceBoundaries
#####################################################################################

package SentenceBoundaries;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $filename) = @_;
  my $self = $class->SUPER::new($logger, 'Segments');
  $self->{__CLASS__} = 'SentenceBoundaries';
  $self->{FILENAME} = $filename;
  $self->{LOGGER} = $logger;
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
    my ($doceid, $segment_id, $start_char, $end_char) =
      map {$entry->get($_)} qw(doceid segment_id start_char end_char);
    my $segments = $self->get("BY_KEY", $doceid);
    my $sentence_boundary = $segments->get("BY_KEY", "$doceid:$segment_id");
    $sentence_boundary->set("SEGMENT_ID", $segment_id);
    $sentence_boundary->set("START_CHAR", $start_char);
    $sentence_boundary->set("END_CHAR", $end_char);
  }
}

sub get_BOUNDARY {
  my ($self, $span_string) = @_;
  my ($id, $sx, $sy, $ex, $ey) = $span_string =~ /^(.*?):\((\d+)\,(\d+)\)-\((\d+)\,(\d+)\)$/;
  if($self->exists($id)) {
    my $segments = $self->get("BY_KEY", $id);
    foreach my $segment($segments->toarray()) {
      my ($start_char, $end_char) = map {$segment->get($_)} qw(START_CHAR END_CHAR);
      return $segment if($sx >= $start_char && $ex <= $end_char);
    }
  }
  0;
}

#####################################################################################
# Segments
#####################################################################################

package Segments;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $filename) = @_;
  my $self = $class->SUPER::new($logger, 'SentenceBoundary');
  $self->{__CLASS__} = 'Segments';
  $self->{FILENAME} = $filename;
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

#####################################################################################
# SentenceBoundary
#####################################################################################

package SentenceBoundary;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = {
    __CLASS__ => 'SentenceBoundary',
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
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
