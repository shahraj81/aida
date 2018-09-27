#!/usr/bin/perl

use warnings;
use strict;
use Encode;
use Carp;

#####################################################################################
# Super
#####################################################################################

package Super;

sub set {
  my ($self, $field, $value) = @_;
  my $method = $self->can("set_$field");
  $method->($self, $value) if $method;
  $self->{$field} = $value unless $method;
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
  IGNORING_LINE                           DEBUG_INFO     Ingoring the line due to a problem: %s
  INVALID_ENTRYPOINT                      FATAL_ERROR    Entrypoint of invalid type %s found
  MISSING_DOCUMENT_ELEMENT                WARNING        Missing document element %s
  MISSING_ENCODING_FORMAT                 FATAL_ERROR    Missing encoding format for document element %s
  MISSING_FILE                            FATAL_ERROR    Could not open %s: %s
  MISSING_RAW_KEY                         FATAL_ERROR    Missing key %s in container of type %s
  MISSING_NODEID_FOR_MENTIONID            WARNING        Missing node_id for nodemention_id %s
  SKIPPING_NODE                           DEBUG_INFO     Skipping node %s because it is not relevant to topic-level hypothesis
  UNDEFINED_VARIABLE                      FATAL_ERROR    Undefined variable %s
  UNEXPECTED_RECORD_DEBUG_INFO_CALL       WARNING        unexpected call to record_debug_info()
  ZEROHOP_QUERY_DEBUG_INFO_01             DEBUG_INFO     Zero-hop query %s corresponds to mention %s of node %s (treeid = %s)
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
  $self->{PROBLEM_COUNTS}{$format->{TYPE}}++;
  my $type = $format->{TYPE};
  my $message = "$type: " . sprintf($format->{FORMAT}, @args);
  # Use Encode to support Unicode.
  $message = Encode::encode_utf8($message);
  my $where = (ref $source ? "$source->{FILENAME} line $source->{LINENUM}" : $source);
  $self->NIST_die("$message\n$where") if $type eq 'FATAL_ERROR' || $type eq 'INTERNAL_ERROR';
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
      # $self->NIST_die("File $output already exists") if -e $output;
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
				print $error_output "\n\n";
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
# LDCNISTMappings
#####################################################################################

package LDCNISTMappings;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $parameters) = @_;
  my $self = {
    CLASS => "LDCNISTMappings",
    PARAMETERS => $parameters,
    ROLE_MAPPINGS => {},
    TYPE_MAPPINGS => {},
    TYPE_CATEGORY => {},
    IS_VALID_ENTRYPOINT => {},
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load_data();
  $self;
}

sub get_LDC_TYPE {
	my ($self, $type, $subtype) = @_;
	
	my $ldc_type = $type;
	$ldc_type = "$ldc_type.$subtype" if $subtype;
	
	$ldc_type;
}

sub get_NIST_TYPE {
	my ($self, $type, $subtype) = @_;
	
	my $key = $type;
	$key = "$key.$subtype" if $subtype;
	
	$self->{TYPE_MAPPINGS}{$key};
}

sub get_NIST_ROLE {
	my ($self, $ldc_role) = @_;
	
	$self->{ROLE_MAPPINGS}{$ldc_role};
}

sub get_NIST_TYPE_CATEGORY {
	my ($self, $nist_type) = @_;

	$self->{TYPE_CATEGORY}{$nist_type};
}

sub is_valid_entrypoint {
	my ($self, $nist_type) = @_;

	$self->{IS_VALID_ENTRYPOINT}{$nist_type};
}

sub load_data {
	my ($self) = @_;
	my ($filename, $filehandler, $header, $entries, $i);
	
	# Load data from role mappings
	$filename = $self->get("PARAMETERS")->get("ROLE_MAPPING_FILE");
	$filehandler = FileHandler->new($self->get("LOGGER"), $filename);
	$header = $filehandler->get("HEADER");
  $entries = $filehandler->get("ENTRIES");
  $i=0;

  foreach my $entry( $entries->toarray() ){
    $i++;
    #print "ENTRY # $i:\n", $entry->tostring(), "\n";
    my $category = $entry->get("category");
    my $ldc_type = $entry->get("ldctype");
    my $ldc_subtype = $entry->get("ldcsubtype");
    my $ldc_role = $entry->get("ldcrole");
    my $nist_type = $entry->get("nisttype");
    my $nist_subtype = $entry->get("nistsubtype");
    my $nist_role = $entry->get("nistrole");
  
    $self->{TYPE_MAPPINGS}{"$ldc_type.$ldc_subtype"} = "$nist_type.$nist_subtype";
    $self->{TYPE_CATEGORY}{"$nist_type.$nist_subtype"} = $category;
  
    my $ldc_fqrolename = "$ldc_type.$ldc_subtype\_$ldc_role";
    my $nist_fqrolename = "$nist_type.$nist_subtype\_$nist_role";
    $self->{ROLE_MAPPINGS}{$ldc_fqrolename} = $nist_fqrolename;
  }
  
  # Load data from type mappings
  $filename = $self->get("PARAMETERS")->get("TYPE_MAPPING_FILE");
  $filehandler = FileHandler->new($self->get("LOGGER"), $filename);
  $header = $filehandler->get("HEADER");
  $entries = $filehandler->get("ENTRIES");
  $i=0;
  
  foreach my $entry( $entries->toarray() ){
    $i++;
    #print "ENTRY # $i:\n", $entry->tostring(), "\n";
    my $ldc_type = $entry->get("LDCTypeOutput");
    my $nist_type = $entry->get("NISTType");
    my $category = $entry->get("Category");
    my $is_valid_entrypoint = $entry->get("IsValidEntrypoint");

    $self->{TYPE_MAPPINGS}{$ldc_type} = $nist_type;  
    $self->{TYPE_CATEGORY}{$nist_type} = $category;
    $self->{IS_VALID_ENTRYPOINT}{$nist_type} = $is_valid_entrypoint;
  }
}

#####################################################################################
# DocumentIDsMappings
#####################################################################################

package DocumentIDsMappings;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $parameters) = @_;
  my $self = {
  	CLASS => "DocumentIDsMappings",
  	PARAMETERS => $parameters,
  	DOCUMENTS => Documents->new($logger),
    DOCUMENTELEMENTS => DocumentElements->new($logger),
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load_data();
  $self;
}

sub load_data {
	my ($self) = @_;
	
	# Load document-element to language mapping
	my %doceid_to_langs_mapping;
	my $filename = $self->get("PARAMETERS")->get("UID_INFO_FILE");
	my $filehandler = FileHandler->new($self->get("LOGGER"), $filename);
	my $header = $filehandler->get("HEADER");
	my $entries = $filehandler->get("ENTRIES");
	foreach my $entry($entries->toarray()) {
		my $doceid = $entry->get("derived_uid");
		my $languages = $entry->get("lang_id");
		$doceid_to_langs_mapping{$doceid} = $languages;
	}
	$filehandler->cleanup();
	
	# Load the DocumentIDsMappingsFile
	my (%doceid_to_docid_mapping, %doceid_to_type_mapping);
	$filename = $self->get("PARAMETERS")->get("DOCUMENTIDS_MAPPING_FILE");
	$filehandler = FileHandler->new($self->get("LOGGER"), $filename);
	$entries = $filehandler->get("ENTRIES");
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
			my $delanguage = $doceid_to_langs_mapping{$document_eid};
			my $detype = $doceid_to_type_mapping{$document_eid};
			my $document = $self->get("DOCUMENTS")->get("BY_KEY", $document_id);
			$document->set("DOCUMENTID", $document_id);
			my $documentelement = $self->get("DOCUMENTELEMENTS")->get("BY_KEY", $document_eid);
			$documentelement->get("DOCUMENTS")->add($document, $document_id);
			$documentelement->set("DOCUMENTELEMENTID", $document_eid);
			$documentelement->set("LANGUAGES", $delanguage);
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
# TheDocumentElements
#    has 1+ 'DocumentElement' contained in the Document
#####################################################################################

package TheDocumentElements;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'DocumentElement');
  $self->{CLASS} = 'TheDocumentElements';
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
# Edges
#####################################################################################

package Edges;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'Edge');
  $self->{CLASS} = 'Edges';
  $self->{EDGE_LOOKUP} = {};
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

sub add {
	my ($self, $value, $key) = @_;
	
	$self->SUPER::add($value, $key);
	push(@{$self->{EDGE_LOOKUP}{SUBJECT}{$value->get("SUBJECT_NODEID")}}, $value); 
	push(@{$self->{EDGE_LOOKUP}{OBJECT}{$value->get("OBJECT_NODEID")}}, $value); 
	push(@{$self->{EDGE_LOOKUP}{PREDICATE}{$value->get("PREDICATE")}}, $value);
	push(@{$self->{EDGE_LOOKUP}
								{"SUBJECT->OBJECT"}
								{$value->get("SUBJECT_NODEID")."->".$value->get("OBJECT_NODEID")}
								{$value->get("PREDICATE")}}, 
			$value);
}

sub toarray {
	my ($self) = @_;
	sort {$a->tostring() cmp $b->tostring()}
		@{$self->{STORE}{LIST} || []};
}

#####################################################################################
# Edge
#####################################################################################

package Edge;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $subject, $nist_role, $object, $attribute, $line) = @_;
  my $self = {
    CLASS => 'Edge',
    SUBJECT => $subject,
    PREDICATE => $nist_role,
    OBJECT => $object,
    ATTRIBUTE => $attribute,
    LINE => $line,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub get_OBJECT_NODEID {
	my ($self) = @_;
	$self->get("OBJECT")->get("NODEID");
}

sub get_SUBJECT_NODEID {
	my ($self) = @_;
	$self->get("SUBJECT")->get("NODEID");
}

sub tostring {
	my ($self) = @_;
	$self->get("SUBJECT_NODEID") . "-" . $self->get("PREDICATE") . "-" . $self->get("OBJECT_NODEID")
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

sub toarray {
	my ($self) = @_;
	sort {$a->get("NODEID") cmp $b->get("NODEID")}
		@{$self->{STORE}{LIST} || []};
}

#####################################################################################
# Node
#####################################################################################

package Node;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = {
    CLASS => 'Node',
    NODEID => undef,
    MENTIONS => Mentions->new($logger),
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub add_mention {
  my ($self, $mention, $mention_id) = @_;
  $self->get("MENTIONS")->add($mention, $mention_id);
}

sub get_LDC_TYPES {
	my ($self) = @_;
	my %hash = map {$_=>1} map {$_->get("LDC_TYPE")} $self->get("MENTIONS")->toarray();
	keys %hash
}

sub get_MENTION {
  my ($self, $mention_id) = @_;
  $self->get("MENTIONS")->get("MENTION", $mention_id);
}


sub get_NIST_TYPES {
	my ($self) = @_;
	my %hash = map {$_=>1} map {$_->get("NIST_TYPE")} $self->get("MENTIONS")->toarray();
	keys %hash;
}

sub get_NIST_TYPE_CATEGORIES {
	my ($self) = @_;
	my %hash = map {$_=>1} map {$_->get("NIST_TYPE_CATEGORY")} $self->get("MENTIONS")->toarray();
	keys %hash;
}

sub get_NIST_TYPE {
	my ($self, $canonical_mention) = @_;
	$self->get("MENTIONS")->get("BY_KEY", $canonical_mention->get("MENTIONID"))->get("NIST_TYPE");
}

sub get_TEXT_STRING {
	my ($self, $canonical_mention) = @_;
	$self->get("MENTIONS")->get("BY_KEY", $canonical_mention->get("MENTIONID"))->get("TEXT_STRING");
}

sub has_compatible_types {
	my ($self) = @_;
	my @type_categories = grep {$_ ne "Filler"} $self->get("NIST_TYPE_CATEGORIES");
	return 0 if @type_categories > 1;
	return 1;
}

#####################################################################################
# Container
#####################################################################################

package Container;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $element_class) = @_;
  
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
# Mentions
#####################################################################################

package Mentions;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'Mention');
  $self->{CLASS} = 'Mentions';
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

sub get_MENTION {
  my ($self, $mention_id) = @_;
  my ($matching_mention) = grep {$_->{MENTIONID} eq $mention_id} $self->toarray();
  $matching_mention || "n/a";
}

sub toarray {
	my ($self) = @_;
	sort {$a->get("MENTIONID") cmp $b->get("MENTIONID")}
		@{$self->{STORE}{LIST} || []};
}

#####################################################################################
# Mention
#####################################################################################

package Mention;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = {
    CLASS => 'Mention',
    LDC_TYPE => undef, 
    NIST_TYPE => undef, 
    MENTIONID => undef,
    TREEID => undef,
    JUSTIFICATIONS => Justifications->new($logger),
    MODALITY => undef,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub add_justification {
  my ($self, $justification) = @_;
  $self->get("JUSTIFICATIONS")->add($justification);
}

sub get_START {
  my ($self) = @_;
  my @starts;
  foreach my $justification($self->get("JUSTIFICATIONS")->toarray()) {
    foreach my $span($justification->get("SPANS")->toarray()) {
      push(@starts, $span->get("START"));
    }
  }
  push(@starts, "nil") unless scalar @starts;
  @starts;
}

sub get_END {
  my ($self) = @_;
  my @ends;
  foreach my $justification($self->get("JUSTIFICATIONS")->toarray()) {
    foreach my $span($justification->get("SPANS")->toarray()) {
      push(@ends, $span->get("END"));
    }
  }
  push(@ends, "nil") unless scalar @ends;
  @ends;
}

sub get_SPANS {
	my ($self) = @_;
	my $spans = Spans->new($self->get("LOGGER"));
	foreach my $justification($self->get("JUSTIFICATIONS")->toarray()) {
		foreach my $span($justification->get("SPANS")->toarray()) {
			$spans->add($span);
		}
	}
	$spans;
}

sub get_SOURCE_DOCUMENT_ELEMENTS {
  my ($self) = @_;
  my @source_doces;
  foreach my $justification($self->get("JUSTIFICATIONS")->toarray()) {
    foreach my $span($justification->get("SPANS")->toarray()) {
      push(@source_doces, $span->get("DOCUMENTEID"));
    }
  }
  @source_doces;
}

#####################################################################################
# Justifications
#####################################################################################

package Justifications;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'Justification');
  $self->{CLASS} = 'Justifications';
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

#####################################################################################
# Justification
#####################################################################################

package Justification;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'Spans');
  $self->{CLASS} = 'Justification';
  $self->{LOGGER} = $logger;
  $self->{SPANS} = Spans->new($self->get("LOGGER"));
  bless($self, $class);
  $self;
}

sub add_span {
  my ($self, $span) = @_;
  $self->get("SPANS")->add($span);
}

#####################################################################################
# Spans
#####################################################################################

package Spans;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'Span');
  $self->{CLASS} = 'Spans';
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

sub toarray {
	my ($self) = @_;
	sort {$a->{DOCUMENTEID} cmp $b->{DOCUMENTEID} ||
					$a->{START} cmp $b->{START} ||
					$a->{END} cmp $b->{END}}
		@{$self->{STORE}{LIST} || []};
}

#####################################################################################
# Span
#####################################################################################

package Span;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $documenteid, $start, $end) = @_;
  $start = "nil" if $start eq "";
  $end = "nil" if $end eq "";
  my $self = {
    CLASS => 'Span',
    DOCUMENTEID => $documenteid,
    START => $start,
    END => $end,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
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
  my $field_separator = $self->get("FIELD_SEPARATOR");
  @{$self->{ELEMENTS}} = split( /$field_separator/, $line);
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

  die("Mismatching column numbers")
    if ($num_of_columns_header != $num_of_columns_entry);

  my $string = "";

  foreach my $i(0..$num_of_columns_entry-1) {
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
# CanonicalMention
#####################################################################################

package CanonicalMention;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $type, $node_id, $mention_id, $keyframe_id, $topic_id, $node) = @_;
  my $self = {
    CLASS => 'CanonicalMention',
    KEYFRAMEID => $keyframe_id,
    MENTIONID => $mention_id,
    NODE => $node,
    NODEID => $node_id,
    TOPICID => $topic_id,
    TYPE => $type,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

#####################################################################################
# CanonicalMentions
#####################################################################################

package CanonicalMentions;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $parameters) = @_;
  my $self = $class->SUPER::new($logger, 'CanonicalMention');
  $self->{CLASS} = 'CanonicalMentions';
  $self->{PARAMETERS} = $parameters;
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

sub get_WHERE {
	my ($self, $field_name, $value) = @_;
	my @retVal;
	foreach my $canonical_mention($self->toarray()) {
		push(@retVal, $canonical_mention)
			if($canonical_mention->get($field_name) eq $value);
	}
	@retVal;
}

sub toarray {
	my ($self) = @_;
	sort {$a->{TOPICID} cmp $b->{TOPICID} ||
					$a->{NODEID} cmp $b->{NODEID} ||
					$a->{MENTIONID} cmp $b->{MENTIONID} ||
					$a->{KEYFRAMEID} cmp $b->{KEYFRAMEID} ||
					$a->{TYPE} cmp $b->{TYPE}}
		@{$self->{STORE}{LIST} || []};
}

#####################################################################################
# Graph
#####################################################################################

package Graph;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $parameters) = @_;
  my $self = {
  	LDC_NIST_MAPPINGS => LDCNISTMappings->new($logger, $parameters),
  	NODES => Nodes->new($logger),
		CANONICAL_MENTIONS => CanonicalMentions->new($logger, $parameters),
  	EDGES => Edges->new($logger),
  	DOCUMENTIDS_MAPPINGS => DocumentIDsMappings->new($logger, $parameters),
  	NODEIDS_LOOKUP => {},
    IMAGES_BOUNDINGBOXES => ImagesBoundingBoxes->new($logger, $parameters),
    KEYFRAMES_BOUNDINGBOXES => KeyFramesBoundingBoxes->new($logger, $parameters),
    ENCODINGFORMAT_TO_MODALITY_MAPPINGS => EncodingFormatToModalityMappings->new($logger, $parameters),
    HYPOTHESIS_RELEVANT_NODEIDS => Container->new($logger, $parameters, "RAW"),
    PARAMETERS => $parameters,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load_data();
  foreach my $node($self->get("NODES")->toarray()) {
  	my $node_id = $node->get("NODEID");
  	my $node_types = join(",", $node->get("NIST_TYPES"));
  }
  $self;
}

sub get_DOCUMENTELEMENTS {
	my ($self) = @_;
	
	$self->get("DOCUMENTIDS_MAPPINGS")->get("DOCUMENTELEMENTS");
}

sub load_data {
	my ($self) = @_;

	$self->load_keyframes_boundingboxes();
	$self->load_images_boundingboxes();
	$self->load_nodes();
	$self->load_edges();
	$self->load_hypothesis_relevant_nodeids();
	$self->load_canonical_mentions();
}

sub load_canonical_mentions {
	my ($self) = @_;

	my $filehandler = FileHandler->new($self->get("LOGGER"), $self->get("PARAMETERS")->get("CANONICAL_MENTIONS_FILE"));
	foreach my $entry($filehandler->get("ENTRIES")->toarray()) {
		my $node_id = $entry->get("node_id");
		my $mention_id = $entry->get("mention_id");
		my $keyframe_id = $entry->get("keyframe_id");
		my $topic_id = $entry->get("topic_id");
		next unless $self->get("NODES")->exists($node_id);
		my $node = $self->get("NODES")->get("BY_KEY", $node_id);
		my $enttype = $node->get("MENTIONS")->get("BY_KEY", $mention_id)->get("NIST_TYPE");
		my %is_valid_entrypoint = %{$self->get("LDC_NIST_MAPPINGS")->get("IS_VALID_ENTRYPOINT")};
		unless (exists $is_valid_entrypoint{$enttype} && $is_valid_entrypoint{$enttype} eq "true") {
			$self->get("LOGGER")->record_problem("INVALID_ENTRYPOINT", $enttype, $entry->get("WHERE"));
			next;
		}
		$self->get("CANONICAL_MENTIONS")->add(CanonicalMention->new($self->get("LOGGER"), "NONSTRING_ENTRYPOINT", $node_id, $mention_id, $keyframe_id, $topic_id, $node));
	}
}

sub load_hypothesis_relevant_nodeids {
	my ($self) = @_;
	# Store the set of nodes relevant to include those nodes that are connected to
	# relevant relation and event nodes by an edge
	my %edge_lookup = %{$self->get("EDGES")->get("EDGE_LOOKUP")};
	foreach my $nodemention_id(keys %{$self->{HYPOTHESIS_RELEVANT_NODEMENTIONIDS}}) {
		my $relevantnode_id = $self->{NODEIDS_LOOKUP}{$nodemention_id};
		unless ($relevantnode_id) {
			my $where = {FILENAME => __FILE__, LINENUM => __LINE__};
			$self->get("LOGGER")->record_problem("MISSING_NODEID_FOR_MENTIONID", $nodemention_id, $where);
			next;
		}
		next if ($self->get("PARAMETERS")->get("IGNORE_NIL") eq "true" && $relevantnode_id =~ /^NIL/);
		$self->get("HYPOTHESIS_RELEVANT_NODEIDS")->add("KEY", $relevantnode_id);
		foreach my $edge(@{$edge_lookup{OBJECT}{$relevantnode_id} || []}) {
			my $connectednode_id = $edge->get("SUBJECT")->get("NODEID");
			next if ($self->get("PARAMETERS")->get("IGNORE_NIL") eq "true" && $connectednode_id =~ /^NIL/);
			# Connected node is also relevant
			$self->get("HYPOTHESIS_RELEVANT_NODEIDS")->add("KEY", $connectednode_id);
		}
		foreach my $edge(@{$edge_lookup{SUBJECT}{$relevantnode_id} || []}) {
			my $connectednode_id = $edge->get("OBJECT")->get("NODEID");
			next if ($self->get("PARAMETERS")->get("IGNORE_NIL") eq "true" && $connectednode_id =~ /^NIL/);
			# Connected node is also relevant
			$self->get("HYPOTHESIS_RELEVANT_NODEIDS")->add("KEY", $connectednode_id);
		}
	}
	# No more need this temporary hash
	delete $self->{HYPOTHESIS_RELEVANT_NODEMENTIONIDS};
}

sub load_images_boundingboxes {
	my ($self) = @_;
	my $filehandler = FileHandler->new($self->get("LOGGER"), $self->get("PARAMETERS")->get("IMAGES_BOUNDINGBOXES_FILE"));
	my $entries = $filehandler->get("ENTRIES");
	foreach my $entry( $entries->toarray() ){
		my $filename = $entry->get("filename");
		my $doceid = $filename;
		$doceid =~ s/\..*?$//;
		my ($bottom_right_x, $bottom_right_y) = (0,0);
		($bottom_right_x, $bottom_right_y) = split(/x/, $entry->get("wxh")) if $entry->get("wxh");
		$self->get("IMAGES_BOUNDINGBOXES")->add(ImageBoundingBox->new($self->get("LOGGER"), $doceid, undef,
												0, 0, $bottom_right_x, $bottom_right_y), $doceid);
	}
}

sub load_keyframes_boundingboxes {
	my ($self) = @_;
	my $filehandler = FileHandler->new($self->get("LOGGER"), $self->get("PARAMETERS")->get("KEYFRAMES_BOUNDINGBOXES_FILE"));
	my $entries = $filehandler->get("ENTRIES");
	foreach my $entry( $entries->toarray() ){
		my ($bottom_right_x, $bottom_right_y) = (0,0);
		($bottom_right_x, $bottom_right_y) = split(/x/, $entry->get("wxh")) if $entry->get("wxh");
		$self->get("KEYFRAMES_BOUNDINGBOXES")->add(KeyFrameBoundingBox->new($self->get("LOGGER"), $entry->get("keyframeid"),
												0, 0,
												$bottom_right_x, $bottom_right_y),
								$entry->get("keyframeid"));
	}
}

sub load_edges {
	my ($self) = @_;
	my ($filehandler, $header, $entries, $i);
	foreach my $filename($self->get("PARAMETERS")->get("EDGES_DATA_FILES")->toarray()) {
		$filehandler = FileHandler->new($self->get("LOGGER"), $filename);
		$header = $filehandler->get("HEADER");
		$entries = $filehandler->get("ENTRIES");
		
		foreach my $entry( $entries->toarray() ){
			my $subject_node_id = $self->{NODEIDS_LOOKUP}{$entry->get("nodemention_id")};
			my $object_node_id = $self->{NODEIDS_LOOKUP}{$entry->get("arg_id")};
			# skip the edge unless you have both ids
			next unless ($subject_node_id && $object_node_id);
			my $subject = $self->get("NODES")->get("BY_KEY", $subject_node_id);
			my @subject_types = $subject->get("LDC_TYPES");
			my $slot_type = $entry->get("slot_type");
			my $attribute = $entry->get("attribute");
			my $object = $self->get("NODES")->get("BY_KEY", $object_node_id);
			
			foreach my $subject_type(@subject_types) {
				my $ldc_role = "$subject_type\_$slot_type";
				my $nist_role = $self->get("LDC_NIST_MAPPINGS")->get("NIST_ROLE", $ldc_role);
				next unless $nist_role;
				my $edge = Edge->new($self->get("LOGGER"), $subject, $nist_role, $object, $attribute, $entry->get("LINE"));
				$self->get("EDGES")->add($edge);
			}
		}
	}
}

sub load_nodes {
	my ($self) = @_;
	my ($filehandler, $header, $entries, $i);
	
	# Load hypothesis file for information about relevant nodes
	my %acceptable_relevance = map {$_=>1} $self->get("PARAMETERS")->get("ACCEPTABLE_RELEVANCE")->toarray();
	my $filename = $self->get("PARAMETERS")->get("HYPOTHESES_FILE");
	$filehandler = FileHandler->new($self->get("LOGGER"), $filename);
	$header = $filehandler->get("HEADER");
	$entries = $filehandler->get("ENTRIES");
	foreach my $entry( $entries->toarray() ){
		next unless $entry->get("hypothesis_id") eq $self->get("PARAMETERS")->get("HYPOTHESISID");
		my $nodemention_id = $entry->get("nodemention_id");
		my $relevance = $entry->get("value");
		next unless $acceptable_relevance{$relevance};
		$self->{HYPOTHESIS_RELEVANT_NODEMENTIONIDS}{$nodemention_id} = 1;
	}
	
	# Load nodes relevant to hypothesis
	foreach my $filename($self->get("PARAMETERS")->get("NODES_DATA_FILES")->toarray()) {
		$filehandler = FileHandler->new($self->get("LOGGER"), $filename);
		$header = $filehandler->get("HEADER");
		$entries = $filehandler->get("ENTRIES"); 
		
		foreach my $entry( $entries->toarray() ){
			my $document_eid = $entry->get("provenance");
			unless ($self->get("DOCUMENTELEMENTS")->exists($document_eid)) {
				$self->get("LOGGER")->record_problem("MISSING_DOCUMENT_ELEMENT", $document_eid, $entry->get("WHERE"));
				$self->get("LOGGER")->record_problem("IGNORING_LINE", $self->get("LINE"), $entry->get("WHERE"));
				next;
			}
			my $thedocumentelement = $self->get("DOCUMENTELEMENTS")->get("BY_KEY", $document_eid);
			my $thedocumentelement_encodingformat = $thedocumentelement->get("TYPE");
			$self->get("LOGGER")->record_problem("MISSING_ENCODING_FORMAT", $document_eid, $entry->get("WHERE"))
				if $thedocumentelement_encodingformat eq "nil";
			my $thedocumentelementmodality = $self->get("ENCODINGFORMAT_TO_MODALITY_MAPPINGS")->get("BY_KEY", 
																										$thedocumentelement_encodingformat);
			my $mention = Mention->new($self->get("LOGGER"));
			my $span = Span->new(
								$self->get("LOGGER"),
								$document_eid,
								$entry->get("textoffset_startchar"),
								$entry->get("textoffset_endchar"),
						);
			my $justification = Justification->new($self->get("LOGGER"));
			$justification->add_span($span);
			$mention->add_justification($justification);
			$mention->set("MODALITY", $thedocumentelementmodality);
			$mention->set("MENTIONID", $entry->get("nodemention_id"));
			$mention->set("DOC_NODEID", $entry->get("document_level_node_id"));
			$mention->set("TEXT_STRING", $entry->get("text_string"));
			$mention->set("JUSTIFICATION_STRING", $entry->get("justification"));
			$mention->set("TYPE", $entry->get("level"));
			$mention->set("TREEID", $entry->get("tree_id"));
			$mention->set("WHERE", $entry->get("WHERE"));
			
			$mention->set("LDC_TYPE", 
							$self->get("LDC_NIST_MAPPINGS")->get("LDC_TYPE", 
								$entry->get("type"), 
								$entry->get("subtype")));
			$mention->set("NIST_TYPE", 
							$self->get("LDC_NIST_MAPPINGS")->get("NIST_TYPE", 
								$entry->get("type"), 
								$entry->get("subtype")));
			$mention->set("NIST_TYPE_CATEGORY",
							$self->get("LDC_NIST_MAPPINGS")->get("NIST_TYPE_CATEGORY",
								$mention->get("NIST_TYPE")));
			my $node = $self->get("NODES")->get("BY_KEY", $entry->get("kb_id"));

			$node->set("NODEID", $entry->get("kb_id")) unless $node->set("NODEID");
			$node->add_mention($mention, $mention->get("MENTIONID"));
			$self->{NODEIDS_LOOKUP}{$entry->get("document_level_node_id")} = $entry->get("kb_id");
			$self->{NODEIDS_LOOKUP}{$entry->get("nodemention_id")} = $entry->get("kb_id");
		}
	}
}

sub generate_queries {
	my ($self) = @_;
	
	$self->generate_class_queries();
	$self->generate_zerohop_queries();
	$self->generate_graph_queries();
}

sub generate_class_queries {
	my ($self) = @_;
	my $queries = ClassQueries->new($self->get("LOGGER"), $self->get("PARAMETERS"));
	my $query_id_prefix = $self->get("PARAMETERS")->get("CLASS_QUERIES_PREFIX");
	my $i = 0;
	my %is_valid_entrypoint = %{$self->get("LDC_NIST_MAPPINGS")->get("IS_VALID_ENTRYPOINT")};
	foreach my $type(sort keys %is_valid_entrypoint) {
		next unless ($is_valid_entrypoint{$type} eq "true");
		$i++;
		my $query_id = "$query_id_prefix\_$i";
		my $query = ClassQuery->new($self->get("LOGGER"), $self->get("PARAMETERS"), $query_id, $type);
		$queries->add($query);
	}
	$queries->write_to_file();
}

sub generate_zerohop_queries {
	my ($self) = @_;
	my $queries = ZeroHopQueries->new($self->get("LOGGER"), $self->get("PARAMETERS"));
	my $query_id_prefix = $self->get("PARAMETERS")->get("ZEROHOP_QUERIES_PREFIX");
	my $i = 0;
	my %is_valid_entrypoint = %{$self->get("LDC_NIST_MAPPINGS")->get("IS_VALID_ENTRYPOINT")};
	foreach my $node($self->get("NODES")->toarray()) {
		foreach my $mention($node->get("MENTIONS")->toarray()){
			my ($canonical_mention) = $self->get("CANONICAL_MENTIONS")->get("WHERE", "MENTIONID", $mention->get("MENTIONID"));
			next unless $canonical_mention;
			next unless $canonical_mention->get("TOPICID") eq $self->get("PARAMETERS")->get("TOPICID");
			my $enttype = $mention->get("NIST_TYPE");
			next unless (exists $is_valid_entrypoint{$enttype} && $is_valid_entrypoint{$enttype} eq "true");
			my $modality = $mention->get("MODALITY");
#			NAMESTRING zerohop queries are out of scope
#			if($mention->get("TYPE") eq "nam") {
#				$i++;
#				my $query_id = "$query_id_prefix\_$i";
#				my $text_string = $mention->get("TEXT_STRING");
#				$self->get("LOGGER")->record_debug_information("ZEROHOP_QUERY_DEBUG_INFO_01", $query_id, $mention->get("MENTIONID"),
#																$node->get("NODEID"), $mention->get("TREEID"), $mention->get("WHERE"));
#				my $query = NameStringZeroHopQuery->new($self->get("LOGGER"),
#											$query_id, $enttype, $text_string);
#				$queries->add($query);
#			}
			foreach my $span($mention->get("SPANS")->toarray()) {
				$i++;
				my $query_id = "$query_id_prefix\_$i";
				my $doceid = $span->get("DOCUMENTEID");
				my $start = $span->get("START");
				my $end = $span->get("END");
				my $keyframe_id = $canonical_mention->get("KEYFRAMEID") if $modality eq "video";
				my $query = NonNameStringZeroHopQuery->new($self->get("LOGGER"),
											$self->get("PARAMETERS"),
											$self->get("KEYFRAMES_BOUNDINGBOXES"),
											$self->get("IMAGES_BOUNDINGBOXES"),
											$query_id, $enttype, $modality, $doceid, $keyframe_id, $start, $end);
				$queries->add($query);
			}
		}
	}	
	$queries->write_to_file();
}

sub generate_graph_queries {
	my ($self) = @_;
	my $queries = GraphQueries->new($self->get("LOGGER"), $self->get("PARAMETERS"));
	$self->generate_all_edges_graph_queries($queries);
	$self->generate_single_edge_graph_queries($queries);
	$queries->write_to_file();
}

sub generate_all_edges_graph_queries {
	my ($self, $queries) = @_;
	my $query_id_prefix = $self->get("PARAMETERS")->get("GRAPH_QUERIES_PREFIX");
	my $i = 0;
	# Edges and node relevant to the hypothesis
	my $edges = Edges->new($self->get("LOGGER"));
	my $nodes = Nodes->new($self->get("LOGGER"));
	foreach my $edge($self->get("EDGES")->toarray()) {
		my $subject = $edge->get("SUBJECT");
		my $object = $edge->get("OBJECT");
		if($subject->has_compatible_types() && $object->has_compatible_types()) {
			if($self->get("HYPOTHESIS_RELEVANT_NODEIDS")->exists($subject->get("NODEID")) &&
			   $self->get("HYPOTHESIS_RELEVANT_NODEIDS")->exists($object->get("NODEID"))) {
			   my $key = $edge->get("PREDICATE") . "(" . $subject->get("NODEID") . "," . $object->get("NODEID") . ")";
			   $edges->add($edge, $key);
			   $nodes->add($subject, $subject->get("NODEID"));
			   $nodes->add($object, $object->get("NODEID"));
			}
		}
	}
	my %strings_used;
	foreach my $node($nodes->toarray()) {
		my @matching_cannoical_mentions = $self->get("CANONICAL_MENTIONS")->get("WHERE", "NODEID", $node->get("NODEID"));
		next unless @matching_cannoical_mentions;
		$i++;
		my $composite_query_id = "$query_id_prefix\_$i\_0";
		my $composite_query = GraphQuery->new($self->get("LOGGER"),
											$self->get("PARAMETERS"),
											"ALL_EDGES_GRAPH_QUERY",
											$self->get("KEYFRAMES_BOUNDINGBOXES"),
											$self->get("IMAGES_BOUNDINGBOXES"),
											$composite_query_id, "DONOT_GENERATE_SPARQL", $edges);
		my $j = 0;
		foreach my $canonical_mention(@matching_cannoical_mentions) {
			next unless $canonical_mention->get("TOPICID") eq $self->get("PARAMETERS")->get("TOPICID");
			$j++;
			my $single_entrypoint_query_id = "$query_id_prefix\_$i\_$j";
			my $single_entrypoint_query = GraphQuery->new($self->get("LOGGER"),
											$self->get("PARAMETERS"),
											"ALL_EDGES_GRAPH_QUERY",
											$self->get("KEYFRAMES_BOUNDINGBOXES"),
											$self->get("IMAGES_BOUNDINGBOXES"),
											$single_entrypoint_query_id, "DONOT_GENERATE_SPARQL", $edges);
			$composite_query->add_entrypoint($canonical_mention);
			$single_entrypoint_query->add_entrypoint($canonical_mention);
			$queries->add($single_entrypoint_query);
			# string entrypoint
			next if $node->get("TEXT_STRING", $canonical_mention) eq "";
			unless($strings_used{$node->get("NODEID")}
				{$node->get("NIST_TYPE", $canonical_mention)}
				{$node->get("TEXT_STRING", $canonical_mention)} && $node->get("TEXT_STRING", $canonical_mention) !~ /^\s+$/) {
					$j++;
					my $string_entrypoint_query_id = "$query_id_prefix\_$i\_$j";
					my $string_entrypoint_query = GraphQuery->new($self->get("LOGGER"),
												$self->get("PARAMETERS"),
												"ALL_EDGES_GRAPH_QUERY",
												$self->get("KEYFRAMES_BOUNDINGBOXES"),
												$self->get("IMAGES_BOUNDINGBOXES"),
												$string_entrypoint_query_id, "DONOT_GENERATE_SPARQL", $edges);
					my $string_entrypoint = {TYPE => "STRING_ENTRYPOINT",
																NODEID => $node->get("NODEID"),
																TOPICID => $self->get("PARAMETERS")->get("TOPICID"),
																NIST_TYPE => $node->get("NIST_TYPE", $canonical_mention), 
																TEXT_STRING => $node->get("TEXT_STRING", $canonical_mention)};
					$string_entrypoint_query->add_entrypoint($string_entrypoint);
					$composite_query->add_entrypoint($string_entrypoint);
					$queries->add($string_entrypoint_query);
					$strings_used{$node->get("NODEID")}
									{$node->get("NIST_TYPE", $canonical_mention)}
									{$node->get("TEXT_STRING", $canonical_mention)} = 1;
				}
		}
		$queries->add($composite_query);
	}
}

sub generate_single_edge_graph_queries {
	my ($self, $queries) = @_;
	my $query_id_prefix = $self->get("PARAMETERS")->get("EDGE_QUERIES_PREFIX");
	my $i = 0;
	foreach my $edge($self->get("EDGES")->toarray()) {
		my $edges = Edges->new($self->get("LOGGER"));
		$edges->add($edge);
		my $subject = $edge->get("SUBJECT");
		my $object = $edge->get("OBJECT");
		if($subject->has_compatible_types() && $object->has_compatible_types()) {
			if($self->get("HYPOTHESIS_RELEVANT_NODEIDS")->exists($subject->get("NODEID")) &&
				$self->get("HYPOTHESIS_RELEVANT_NODEIDS")->exists($object->get("NODEID"))) {
				my $key = $edge->get("PREDICATE") . "(" . $subject->get("NODEID") . "," . $object->get("NODEID") . ")";
				my %strings_used;
				foreach my $node(($subject, $object)) {
					my @matching_cannoical_mentions = $self->get("CANONICAL_MENTIONS")->get("WHERE", "NODEID", $node->get("NODEID"));
					next unless @matching_cannoical_mentions;
					$i++;
					my $composite_query_id = "$query_id_prefix\_$i\_0";
					my $composite_query = GraphQuery->new($self->get("LOGGER"),
											$self->get("PARAMETERS"),
											"SINGLE_EDGE_GRAPH_QUERY",
											$self->get("KEYFRAMES_BOUNDINGBOXES"),
											$self->get("IMAGES_BOUNDINGBOXES"),
											$composite_query_id, "DONOT_GENERATE_SPARQL", $edges);
					my $j = 0;
					foreach my $canonical_mention(@matching_cannoical_mentions) {
						next unless $canonical_mention->get("TOPICID") eq $self->get("PARAMETERS")->get("TOPICID");
						$j++;
						my $single_entrypoint_query_id = "$query_id_prefix\_$i\_$j";
						my $single_entrypoint_query = GraphQuery->new($self->get("LOGGER"),
											$self->get("PARAMETERS"),
											"SINGLE_EDGE_GRAPH_QUERY",
											$self->get("KEYFRAMES_BOUNDINGBOXES"),
											$self->get("IMAGES_BOUNDINGBOXES"),
											$single_entrypoint_query_id, "DO_GENERATE_SPARQL", $edges);
						$composite_query->add_entrypoint($canonical_mention);
						$single_entrypoint_query->add_entrypoint($canonical_mention);
						$queries->add($single_entrypoint_query);
						# string entrypoint
						next if $node->get("TEXT_STRING", $canonical_mention) eq "";
						unless($strings_used{$node->get("NODEID")}
									{$node->get("NIST_TYPE", $canonical_mention)}
									{$node->get("TEXT_STRING", $canonical_mention)} && $node->get("TEXT_STRING", $canonical_mention) !~ /^\s+$/) {
							$j++;
							my $string_entrypoint_query_id = "$query_id_prefix\_$i\_$j";
							my $string_entrypoint_query = GraphQuery->new($self->get("LOGGER"),
												$self->get("PARAMETERS"),
												"SINGLE_EDGE_GRAPH_QUERY",
												$self->get("KEYFRAMES_BOUNDINGBOXES"),
												$self->get("IMAGES_BOUNDINGBOXES"),
												$string_entrypoint_query_id, "DO_GENERATE_SPARQL", $edges);
							my $string_entrypoint = {TYPE => "STRING_ENTRYPOINT",
																NODEID => $node->get("NODEID"),
																TOPICID => $self->get("PARAMETERS")->get("TOPICID"),
																NIST_TYPE => $node->get("NIST_TYPE", $canonical_mention), 
																TEXT_STRING => $node->get("TEXT_STRING", $canonical_mention)};
							$string_entrypoint_query->add_entrypoint($string_entrypoint);
							$composite_query->add_entrypoint($string_entrypoint);
							$queries->add($string_entrypoint_query);
							$strings_used{$node->get("NODEID")}
											{$node->get("NIST_TYPE", $canonical_mention)}
											{$node->get("TEXT_STRING", $canonical_mention)} = 1;
						}
					}
					$queries->add($composite_query);
				}
			}
		}
	}
}

#####################################################################################
# ImagesBoundingBoxes
#####################################################################################

package ImagesBoundingBoxes;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $parameters) = @_;
  my $self = $class->SUPER::new($logger, 'ImageBoundingBox');
  $self->{CLASS} = 'ImagesBoundingBoxes';
  $self->{PARAMETERS} = $parameters;
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

#####################################################################################
# ImageBoundingBox
#####################################################################################

package ImageBoundingBox;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $doceid, $type, $top_left_x, $top_left_y, $bottom_right_x, $bottom_right_y) = @_;
  my $self = {
    CLASS => 'ImageBoundingBox',
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

#####################################################################################
# KeyFramesBoundingBoxes
#####################################################################################

package KeyFramesBoundingBoxes;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $parameters) = @_;
  my $self = $class->SUPER::new($logger, 'KeyFrameBoundingBox');
  $self->{CLASS} = 'KeyFramesBoundingBoxes';
  $self->{PARAMETERS} = $parameters;
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
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
    CLASS => 'KeyFrameBoundingBox',
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

#####################################################################################
# ClassQueries
#####################################################################################

package ClassQueries;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $parameters) = @_;
  my $self = $class->SUPER::new($logger, 'ClassQuery');
  $self->{CLASS} = 'ClassQueries';
  $self->{PARAMETERS} = $parameters;
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

sub write_to_file {
	my ($self) = @_;
	my $output_filename_xml = $self->get("PARAMETERS")->get("CLASS_QUERIES_XML_OUTPUT_FILE");
	open(my $program_output_xml, ">:utf8", $output_filename_xml) or die("Could not open $output_filename_xml: $!");
	print $program_output_xml "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
	print $program_output_xml "<class_queries>\n";
	foreach my $query($self->toarray()) {
		$query->write_to_file($program_output_xml);
	}
	print $program_output_xml "<\/class_queries>\n";
	close($program_output_xml);
}

sub toarray {
	my ($self) = @_;
	sort {$a->get("NUMERIC_ID") <=> $b->get("NUMERIC_ID")}
		@{$self->{STORE}{LIST} || []};
}

#####################################################################################
# ClassQuery
#####################################################################################

package ClassQuery;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $parameters, $query_id, $enttype) = @_;
  my $self = {
    CLASS => 'ClassQuery',
    PARAMETERS => $parameters,
    QUERY_ID => $query_id,
    ENTTYPE => $enttype,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub get_NUMERIC_ID {
	my ($self) = @_;
	my $prefix = $self->get("PARAMETERS")->get("CLASS_QUERIES_PREFIX");
	my ($numeric_id) = $self->get("QUERY_ID") =~ /^$prefix\_(\d+)$/;
	$numeric_id;
}

sub write_to_file {
	my ($self, $program_output) = @_;
	my $query_id = $self->get("QUERY_ID");
	my $enttype = $self->get("ENTTYPE");

	my $attributes = XMLAttributes->new($self->get("LOGGER"));
	$attributes->add("$query_id", "id");

	my $xml_enttype = XMLElement->new($self->get("LOGGER"), $enttype, "enttype", 0);

	my $sparql = <<'END_SPARQL_QUERY';

	<![CDATA[
	PREFIX ldcOnt: <https://tac.nist.gov/tracks/SM-KBP/2018/ontologies/SeedlingOntology#>
	PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
	PREFIX aida:  <https://tac.nist.gov/tracks/SM-KBP/2018/ontologies/InterchangeOntology#>
	PREFIX xsd:   <http://www.w3.org/2001/XMLSchema#>

	# Query: QUERYID
	# Query description: Find all mentions of type ENTTYPE

	SELECT ?doceid ?sid ?kfid ?so ?eo ?ulx ?uly ?lrx ?lry ?st ?et ?cv
	WHERE {
			?statement1    a                    rdf:Statement .
			?statement1    rdf:object           ldcOnt:ENTTYPE .
			?statement1    rdf:predicate        rdf:type .
			?statement1    aida:justifiedBy     ?justification .
			?justification aida:source          ?doceid .
			?justification aida:confidence      ?confidence .
			?confidence    aida:confidenceValue ?cv .

			OPTIONAL { ?justification a                           aida:TextJustification .
					   ?justification aida:startOffset            ?so .
					   ?justification aida:endOffsetInclusive     ?eo }

			OPTIONAL { ?justification a                           aida:ImageJustification .
					   ?justification aida:boundingBox            ?bb  .
					   ?bb            aida:boundingBoxUpperLeftX  ?ulx .
					   ?bb            aida:boundingBoxUpperLeftY  ?uly .
					   ?bb            aida:boundingBoxLowerRightX ?lrx .
					   ?bb            aida:boundingBoxLowerRightY ?lry }

			OPTIONAL { ?justification a                           aida:KeyFrameVideoJustification .
					   ?justification aida:keyFrame               ?kfid .
					   ?justification aida:boundingBox            ?bb  .
					   ?bb            aida:boundingBoxUpperLeftX  ?ulx .
					   ?bb            aida:boundingBoxUpperLeftY  ?uly .
					   ?bb            aida:boundingBoxLowerRightX ?lrx .
					   ?bb            aida:boundingBoxLowerRightY ?lry }

			OPTIONAL { ?justification a                           aida:ShotVideoJustification .
					   ?justification aida:shot                   ?sid }

			OPTIONAL { ?justification a                           aida:AudioJustification .
					   ?justification aida:startTimestamp         ?st .
					   ?justification aida:endTimestamp           ?et }

	}
	]]>

END_SPARQL_QUERY

	$sparql =~ s/QUERYID/$query_id/g;
	$sparql =~ s/ENTTYPE/$enttype/g;
	my $xml_sparql = XMLElement->new($self->get("LOGGER"), $sparql, "sparql", 1);
	my $xml_query = XMLElement->new($self->get("LOGGER"),
			XMLContainer->new($self->get("LOGGER"), $xml_enttype, $xml_sparql),
			"class_query", 1, $attributes);
	print $program_output $xml_query->tostring(2);
}

#####################################################################################
# ZeroHopQueries
#####################################################################################

package ZeroHopQueries;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $parameters) = @_;
  my $self = $class->SUPER::new($logger, 'ZeroHopQuery');
  $self->{CLASS} = 'ZeroHopQueries';
  $self->{PARAMETERS} = $parameters;
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

sub write_to_file {
	my ($self) = @_;
	my $output_filename_xml = $self->get("PARAMETERS")->get("ZEROHOP_QUERIES_XML_OUTPUT_FILE");
	open(my $program_output_xml, ">:utf8", $output_filename_xml) or die("Could not open $output_filename_xml: $!");
	print $program_output_xml "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
	print $program_output_xml "<zerohop_queries>\n";
	foreach my $query($self->toarray()) {
		$query->write_to_file($program_output_xml);
	}
	print $program_output_xml "<\/zerohop_queries>\n";
	close($program_output_xml);
}

sub toarray {
	my ($self) = @_;
	sort {$a->get("NUMERIC_ID") <=> $b->get("NUMERIC_ID")}
		@{$self->{STORE}{LIST} || []};
}

#####################################################################################
# NameStringZeroHopQuery
# These are currently out of scope
#####################################################################################
#
#package NameStringZeroHopQuery;
#
#use parent -norequire, 'Super';
#
#sub new {
#  my ($class, $logger, $query_id, $enttype, $name_string) = @_;
#  my $self = {
#    CLASS => 'NameStringZeroHopQuery',
#    QUERY_ID => $query_id,
#    ENTTYPE => $enttype,
#    NAME_STRING => $name_string,
#    LOGGER => $logger,
#  };
#  bless($self, $class);
#  $self;
#}
#
#sub write_to_file {
#	my ($self, $program_output) = @_;
#	my $logger = $self->get("LOGGER");
#	my $query_id = $self->get("QUERY_ID");
#	my $enttype = $self->get("ENTTYPE");
#	my $name_string = $self->get("NAME_STRING");
#
#	my $xml_node = XMLElement->new($logger, "?node", "node", 0);
#	my $xml_enttype = XMLElement->new($logger, $enttype, "enttype", 0);
#	my $xml_namestring = XMLElement->new($logger, $name_string, "name_string", 0);
#	my $xml_descriptor = XMLElement->new(
#			$logger,
#			XMLContainer->new($logger, $xml_namestring),
#			"string_descriptor",
#			1);
#	my $attributes = XMLAttributes->new($logger);
#	$attributes->add("$query_id", "id");
#	my $xml_entrypoint = XMLElement->new($logger,
#			XMLContainer->new($logger, $xml_node, $xml_enttype, $xml_descriptor),
#			"entrypoint", 1);
#
#	my $sparql = <<'END_SPARQL_QUERY';
#
#	<![CDATA[
#	SELECT ?nid ?doceid ?sid ?kfid ?so ?eo ?ulx ?uly ?brx ?bry ?st ?et ?cv
#	WHERE {
#			?statement1    a                    rdf:Statement .
#			?statement1    rdf:object           ldcOnt:ENTTYPE .
#			?statement1    rdf:predicate        rdf:type .
#			?statement1    rdf:subject          ?nid .
#			?statement1    aida:justifiedBy     ?justification .
#			?justification aida:source          ?doceid .
#			?justification aida:confidence      ?confidence .
#			?confidence    aida:confidenceValue ?cv .
#			?nid           a                    aida:Entity .
#			?nid           aida:hasName         "NAME_STRING" .
#
#			OPTIONAL { ?justification a                           aida:TextJustification .
#					   ?justification aida:startOffset            ?so .
#					   ?justification aida:endOffsetInclusive     ?eo }
#
#			OPTIONAL { ?justification a                           aida:ImageJustification .
#					   ?justification aida:boundingBox            ?bb  .
#					   ?bb            aida:boundingBoxUpperLeftX  ?ulx .
#					   ?bb            aida:boundingBoxUpperLeftY  ?uly .
#					   ?bb            aida:boundingBoxLowerRightX ?brx .
#					   ?bb            aida:boundingBoxLowerRightY ?bry }
#
#			OPTIONAL { ?justification a                           aida:KeyFrameVideoJustification .
#					   ?justification aida:keyFrame               ?kfid .
#					   ?justification aida:boundingBox            ?bb  .
#					   ?bb            aida:boundingBoxUpperLeftX  ?ulx .
#					   ?bb            aida:boundingBoxUpperLeftY  ?uly .
#					   ?bb            aida:boundingBoxLowerRightX ?brx .
#					   ?bb            aida:boundingBoxLowerRightY ?bry }
#
#			OPTIONAL { ?justification a                           aida:ShotVideoJustification .
#					   ?justification aida:shot                   ?sid }
#
#			OPTIONAL { ?justification a                           aida:AudioJustification .
#					   ?justification aida:startTimestamp         ?st .
#					   ?justification aida:endTimestamp           ?et }
#
#	}
#	]]>
#
#END_SPARQL_QUERY
#
#	$sparql =~ s/QUERYID/$query_id/g;
#	$sparql =~ s/ENTTYPE/$enttype/g;
#	$sparql =~ s/NAME_STRING/$name_string/;
#	my $xml_sparql = XMLElement->new($self->get("LOGGER"), $sparql, "sparql", 1);
#
#	my $xml_query = XMLElement->new($logger,
#																	XMLContainer->new($logger, $xml_entrypoint, $xml_sparql),
#																	"zerohop_query", 1, $attributes);
#	print $program_output $xml_query->tostring(2);
#}

#####################################################################################
# NonNameStringZeroHopQuery
#####################################################################################

package NonNameStringZeroHopQuery;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $parameters, $keyframes_boundingboxes, $images_boundingboxes, $query_id, $enttype, $modality, $doceid, $keyframe_id, $start, $end) = @_;
  my $self = {
    CLASS => 'NonNameStringZeroHopQuery',
    PARAMETERS => $parameters,
    KEYFRAMES_BOUNDINGBOXES => $keyframes_boundingboxes,
    IMAGES_BOUNDINGBOXES => $images_boundingboxes,
    QUERY_ID => $query_id,
    ENTTYPE => $enttype,
    DOCUMENTELEMENTID => $doceid,
    KEYFRAMEID => $keyframe_id,
    MODALITY => $modality,
    START => $start,
    END => $end,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub get_NUMERIC_ID {
	my ($self) = @_;
	my $prefix = $self->get("PARAMETERS")->get("ZEROHOP_QUERIES_PREFIX");
	my ($numeric_id) = $self->get("QUERY_ID") =~ /^$prefix\_(\d+)$/;
	$numeric_id;
}

sub write_to_file {
	my ($self, $program_output) = @_;
	my $logger = $self->get("LOGGER");
	my $query_id = $self->get("QUERY_ID");
	my $enttype = $self->get("ENTTYPE");
	my $doceid = $self->get("DOCUMENTELEMENTID");
	my $modality = $self->get("MODALITY");
	my $start = $self->get("START");
	my $end = $self->get("END");
	my $fn_manager = FieldNameManager->new($self->get("LOGGER"), $modality);
	my ($keyframeid, $xml_keyframeid);
	if($modality eq "video") {
		$keyframeid = $self->get("KEYFRAMEID");
		my $keyframe_boundingbox = $self->get("KEYFRAMES_BOUNDINGBOXES")->get("BY_KEY", $keyframeid);
		$start = $keyframe_boundingbox->get("START");
		$end = $keyframe_boundingbox->get("END");
		$xml_keyframeid = XMLElement->new($logger, $keyframeid, "keyframeid", 0);
	}
	if($modality eq "image") {
		my $image_boundingbox = $self->get("IMAGES_BOUNDINGBOXES")->get("BY_KEY", $doceid);
		$start = $image_boundingbox->get("START");
		$end = $image_boundingbox->get("END");
	}
	my $xml_node = XMLElement->new($logger, "?node", "node", 0);
	my $xml_enttype = XMLElement->new($logger, $enttype, "enttype", 0);
	my $xml_doceid = XMLElement->new($logger, $doceid, "doceid", 0);
	my $xml_start = XMLElement->new($logger, $start, $fn_manager->get("FIELDNAME", "start"), 0);
	my $xml_end = XMLElement->new($logger, $end, $fn_manager->get("FIELDNAME", "end"), 0);
	my $xml_descriptor;
	$xml_descriptor = XMLElement->new(
			$logger,
			XMLContainer->new($logger, $xml_doceid, $xml_start, $xml_end),
			$fn_manager->get("FIELDNAME", "descriptor"),
			1);
	$xml_descriptor = XMLElement->new(
			$logger,
			XMLContainer->new($logger, $xml_doceid, $xml_keyframeid, $xml_start, $xml_end),
			$fn_manager->get("FIELDNAME", "descriptor"),
			1) if $modality eq "video";
	my $xml_entrypoint = XMLElement->new(
			$logger, 
			XMLContainer->new($logger, $xml_node, $xml_enttype, $xml_descriptor), 
			"entrypoint",
			1);
	my $attributes = XMLAttributes->new($logger);
	$attributes->add("$query_id", "id");

	my $text_entrypoint_constraints = <<'TEXT_ENTRYPOINT_CONSTRAINTS';
?justification_ep a                         aida:TextJustification .
		?justification_ep aida:source               "DOCEID" .
		?justification_ep aida:startOffset          ?epso .
		?justification_ep aida:endOffsetInclusive   ?epeo .
		FILTER ( (?epeo >= START_OFFSET && $epeo <= END_OFFSET) || (?epso >= START_OFFSET && ?epso <= END_OFFSET) ) .
TEXT_ENTRYPOINT_CONSTRAINTS

	my $image_entrypoint_constraints = <<'IMAGE_ENTRYPOINT_CONSTRAINTS';
?justification_ep a                         aida:ImageJustification .
		?justification_ep aida:source               "DOCEID" .
		?justification_ep aida:boundingBox          ?boundingbox_ep .
		?boundingbox_ep aida:boundingBoxUpperLeftX  ?epulx .
		?boundingbox_ep aida:boundingBoxUpperLeftY  ?epuly .
		?boundingbox_ep aida:boundingBoxLowerRightX ?eplrx .
		?boundingbox_ep aida:boundingBoxLowerRightY ?eplry .
		FILTER ((?epulx >= UPPER_LEFT_X && ?epulx <= LOWER_RIGHT_X && ?epuly <= LOWER_RIGHT_Y && ?epuly >= UPPER_LEFT_Y) ||
			(?eplrx >= UPPER_LEFT_X && ?eplrx <= LOWER_RIGHT_X && ?eplry <= LOWER_RIGHT_Y && ?eplry >= UPPER_LEFT_Y) ||
			(?eplrx >= UPPER_LEFT_X && ?eplrx <= LOWER_RIGHT_X && ?epuly <= LOWER_RIGHT_Y && ?epuly >= UPPER_LEFT_Y) ||
			(?epulx >= UPPER_LEFT_X && ?epulx <= LOWER_RIGHT_X && ?eplry <= LOWER_RIGHT_Y && ?eplry >= UPPER_LEFT_Y)) .
IMAGE_ENTRYPOINT_CONSTRAINTS

	my $video_entrypoint_constraints = <<'VIDEO_ENTRYPOINT_CONSTRAINTS';
?justification_ep a                         aida:KeyFrameVideoJustification .
		?justification_ep aida:source               "DOCEID" .
		?justification_ep aida:keyFrame             "KEYFRAMEID" .
		?justification_ep aida:boundingBox          ?boundingbox_ep .
		?boundingbox_ep aida:boundingBoxUpperLeftX  ?epulx .
		?boundingbox_ep aida:boundingBoxUpperLeftY  ?epuly .
		?boundingbox_ep aida:boundingBoxLowerRightX ?eplrx .
		?boundingbox_ep aida:boundingBoxLowerRightY ?eplry .
		FILTER ((?epulx >= UPPER_LEFT_X && ?epulx <= LOWER_RIGHT_X && ?epuly <= LOWER_RIGHT_Y && ?epuly >= UPPER_LEFT_Y) ||
			(?eplrx >= UPPER_LEFT_X && ?eplrx <= LOWER_RIGHT_X && ?eplry <= LOWER_RIGHT_Y && ?eplry >= UPPER_LEFT_Y) ||
			(?eplrx >= UPPER_LEFT_X && ?eplrx <= LOWER_RIGHT_X && ?epuly <= LOWER_RIGHT_Y && ?epuly >= UPPER_LEFT_Y) ||
			(?epulx >= UPPER_LEFT_X && ?epulx <= LOWER_RIGHT_X && ?eplry <= LOWER_RIGHT_Y && ?eplry >= UPPER_LEFT_Y)) .
VIDEO_ENTRYPOINT_CONSTRAINTS

	my $audio_entrypoint_constrinats = <<'AUDIO_ENTRYPOINT_CONSTRAINTS';
?justification_ep a                       aida:AudioJustification .
		?justification_ep aida:source             "DOCEID" .
		?justification_ep aida:startTimestamp     ?epst .
		?justification_ep aida:endTimestamp       ?epet .
		FILTER ( (?epet >= START_TIME && $epet <= END_TIME) || (?epst >= START_TIME && ?epst <= END_TIME) ) .
AUDIO_ENTRYPOINT_CONSTRAINTS

	my $sparql = <<'END_SPARQL_QUERY';

	<![CDATA[
	PREFIX ldcOnt: <https://tac.nist.gov/tracks/SM-KBP/2018/ontologies/SeedlingOntology#>
	PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
	PREFIX aida:  <https://tac.nist.gov/tracks/SM-KBP/2018/ontologies/InterchangeOntology#>
	PREFIX xsd:   <http://www.w3.org/2001/XMLSchema#>

	# Query: QUERYID

	SELECT ?cluster ?doceid ?sid ?kfid ?so ?eo ?ulx ?uly ?brx ?bry ?st ?et ?cm1cv ?cm2cv ?cv
	WHERE {
		?statement1    a                    rdf:Statement .
		?statement1    rdf:object           ldcOnt:ENTTYPE .
		?statement1    rdf:predicate        rdf:type .
		?statement1    rdf:subject          ?nid_ot .
		?statement1    aida:justifiedBy     ?justification .
		?justification aida:source          ?doceid .
		?justification aida:confidence      ?confidence .
		?confidence    aida:confidenceValue ?cv .

		?cluster        a                    aida:SameAsCluster .
		?statement2     a                    aida:ClusterMembership .
		?statement2     aida:cluster         ?cluster .
		?statement2     aida:clusterMember   ?nid_ep .
		?statement2     aida:confidence      ?cm1_confidence .
		?cm1_confidence aida:confidenceValue ?cm1cv .

		?statement3     a                    aida:ClusterMembership .
		?statement3     aida:cluster         ?cluster .
		?statement3     aida:clusterMember   ?nid_ot .
		?statement3     aida:confidence      ?cm2_confidence .
		?cm2_confidence aida:confidenceValue ?cm2cv .

		?statement4       a                         rdf:Statement .
		?statement4       rdf:object                ldcOnt:ENTTYPE .
		?statement4       rdf:predicate             rdf:type .
		?statement4       rdf:subject               ?nid_ep .
		?statement4       aida:justifiedBy          ?justification_ep .
		ENTRYPOINT_CONSTRAINTS

		OPTIONAL { ?justification a                  aida:TextJustification .
			?justification aida:startOffset            ?so .
			?justification aida:endOffsetInclusive     ?eo }

		OPTIONAL { ?justification a                  aida:ImageJustification .
			?justification aida:boundingBox            ?bb  .
			?bb            aida:boundingBoxUpperLeftX  ?ulx .
			?bb            aida:boundingBoxUpperLeftY  ?uly .
			?bb            aida:boundingBoxLowerRightX ?brx .
			?bb            aida:boundingBoxLowerRightY ?bry }

		OPTIONAL { ?justification a                  aida:KeyFrameVideoJustification .
			?justification aida:keyFrame               ?kfid .
			?justification aida:boundingBox            ?bb  .
			?bb            aida:boundingBoxUpperLeftX  ?ulx .
			?bb            aida:boundingBoxUpperLeftY  ?uly .
			?bb            aida:boundingBoxLowerRightX ?brx .
			?bb            aida:boundingBoxLowerRightY ?bry }

		OPTIONAL { ?justification a                  aida:ShotVideoJustification .
			?justification aida:shot                   ?sid }

		OPTIONAL { ?justification a                  aida:AudioJustification .
			?justification aida:startTimestamp         ?st .
			?justification aida:endTimestamp           ?et }

	}
	]]>

END_SPARQL_QUERY

	if($modality eq "text") {
		$text_entrypoint_constraints =~ s/START_OFFSET/$start/g;
		$text_entrypoint_constraints =~ s/END_OFFSET/$end/g;
		$sparql =~ s/ENTRYPOINT_CONSTRAINTS/$text_entrypoint_constraints/;
	}
	elsif($modality eq "image") {
		my ($ulx, $uly) = split(",", $start);
		my ($lrx, $lry) = split(",", $end);
		$image_entrypoint_constraints =~ s/UPPER_LEFT_X/$ulx/g;
		$image_entrypoint_constraints =~ s/UPPER_LEFT_Y/$uly/g;
		$image_entrypoint_constraints =~ s/LOWER_RIGHT_X/$lrx/g;
		$image_entrypoint_constraints =~ s/LOWER_RIGHT_Y/$lry/g;
		$sparql =~ s/ENTRYPOINT_CONSTRAINTS/$image_entrypoint_constraints/;
	}
	elsif($modality eq "video") {
		my ($ulx, $uly) = split(",", $start);
		my ($lrx, $lry) = split(",", $end);
		$video_entrypoint_constraints =~ s/UPPER_LEFT_X/$ulx/g;
		$video_entrypoint_constraints =~ s/UPPER_LEFT_Y/$uly/g;
		$video_entrypoint_constraints =~ s/LOWER_RIGHT_X/$lrx/g;
		$video_entrypoint_constraints =~ s/LOWER_RIGHT_Y/$lry/g;
		$video_entrypoint_constraints =~ s/KEYFRAMEID/$keyframeid/g;
		$sparql =~ s/ENTRYPOINT_CONSTRAINTS/$video_entrypoint_constraints/;
	}
	elsif($modality eq "audio") {
		$audio_entrypoint_constrinats =~ s/START_TIME/$start/g;
		$audio_entrypoint_constrinats =~ s/END_TIME/$end/g;
		$sparql =~ s/ENTRYPOINT_CONSTRAINTS/$audio_entrypoint_constrinats/;
	}

	$sparql =~ s/QUERYID/$query_id/g;
	$sparql =~ s/ENTTYPE/$enttype/g;
	$sparql =~ s/DOCEID/$doceid/g;
	my $xml_sparql = XMLElement->new($self->get("LOGGER"), $sparql, "sparql", 1);

	my $xml_query = XMLElement->new($logger,
						XMLContainer->new($logger, $xml_entrypoint, $xml_sparql),
						"zerohop_query", 1, $attributes);
	print $program_output $xml_query->tostring(2);
}

#####################################################################################
# GraphQueries
#####################################################################################

package GraphQueries;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $parameters) = @_;
  my $self = $class->SUPER::new($logger, 'GraphQuery');
  $self->{CLASS} = 'GraphQueries';
  $self->{PARAMETERS} = $parameters;
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

sub write_to_file {
	my ($self) = @_;
	my $output_filename_xml = $self->get("PARAMETERS")->get("GRAPH_QUERIES_XML_OUTPUT_FILE");
	open(my $program_output_xml, ">:utf8", $output_filename_xml) or die("Could not open $output_filename_xml: $!");
	print $program_output_xml "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
	print $program_output_xml "<graph_queries>\n";
	foreach my $query($self->toarray()) {
		$query->write_to_file($program_output_xml);
	}
	print $program_output_xml "<\/graph_queries>\n";
	close($program_output_xml);
}

sub toarray {
	my ($self) = @_;
	sort {$a->get("NUMERIC_ID", "P1") <=> $b->get("NUMERIC_ID", "P1") ||
		$a->get("NUMERIC_ID", "P2") <=> $b->get("NUMERIC_ID", "P2")}
		@{$self->{STORE}{LIST} || []};
}

#####################################################################################
# GraphQuery
#####################################################################################

package GraphQuery;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $parameters, $type, $keyframes_boundingboxes, $images_boundingboxes, $query_id, $generate_sparql, $edges) = @_;
  my $self = {
    CLASS => 'GraphQuery',
    PARAMETERS => $parameters,
    KEYFRAMES_BOUNDINGBOXES => $keyframes_boundingboxes,
    IMAGES_BOUNDINGBOXES => $images_boundingboxes,
    QUERY_ID => $query_id,
    EDGES => $edges,
    ENTRYPOINTS => [],
    GENERATE_SPARQL => undef,
    TYPE => $type,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->set("GENERATE_SPARQL", 1) if($generate_sparql eq "DO_GENERATE_SPARQL");
  $self->set("GENERATE_SPARQL", 0) if($generate_sparql eq "DONOT_GENERATE_SPARQL");
  $self;
}

sub get_NUMERIC_ID {
	my ($self, $part_num) = @_;
	my $prefix;
	$prefix = $self->get("PARAMETERS")->get("GRAPH_QUERIES_PREFIX") if $self->get("TYPE") eq "ALL_EDGES_GRAPH_QUERY";
	$prefix = $self->get("PARAMETERS")->get("EDGE_QUERIES_PREFIX") if $self->get("TYPE") eq "SINGLE_EDGE_GRAPH_QUERY";
	my ($numeric_id_p1, $numeric_id_p2) = $self->get("QUERY_ID") =~ /^$prefix\_(\d+?)_(\d+?)$/;
	return $numeric_id_p1 if $part_num eq "P1";
	return $numeric_id_p2 if $part_num eq "P2";
}

sub add_entrypoint {
	my ($self, $canonical_mention) = @_;
	push(@{$self->{ENTRYPOINTS}}, $canonical_mention);
}

sub write_to_file {
	my ($self, $program_output) = @_;
	my $logger = $self->get("LOGGER");
	my $query_id = $self->get("QUERY_ID");
	my $query_attributes = XMLAttributes->new($logger);
	$query_attributes->add("$query_id", "id");
	# process the edges into a graph
	my $xml_edges_container = XMLContainer->new($logger);
	my $edge_id = 0;
	foreach my $edge($self->get("EDGES")->toarray()) {
		$edge_id++;
		my $subject = &mask($edge->get("SUBJECT")->get("NODEID"));
		my $object = &mask($edge->get("OBJECT")->get("NODEID"));
		my $predicate = $edge->get("PREDICATE");
		my $xml_subject = XMLElement->new($logger, $subject, "subject", 0);
		my $xml_object = XMLElement->new($logger, $object, "object", 0);
		my $xml_predicate = XMLElement->new($logger, $predicate, "predicate", 0);
		my $edge_attributes = XMLAttributes->new($logger);
		$edge_attributes->add("$edge_id", "id");
		my $xml_edge = XMLElement->new(
							$logger,
							XMLContainer->new($logger, $xml_subject, $xml_predicate, $xml_object),
							"edge",
							1,
							$edge_attributes);
		$xml_edges_container->add($xml_edge);
	}
	my $xml_edges = XMLElement->new($logger, $xml_edges_container, "edges", 1);
	my $xml_graph = XMLElement->new($logger, $xml_edges, "graph", 1);
	# process the entrypoints
	my $xml_entrypoints_container = XMLContainer->new($logger);
	foreach my $entrypoint(@{$self->get("ENTRYPOINTS")}) {
		if($entrypoint->{TYPE} eq "STRING_ENTRYPOINT") {
			my $node_id = &mask($entrypoint->{"NODEID"});
			my $enttype = $entrypoint->{"NIST_TYPE"};
			my $name_string = $entrypoint->{"TEXT_STRING"};
			my $xml_node = XMLElement->new($logger, $node_id, "node", 0);
			my $xml_enttype = XMLElement->new($logger, $enttype, "enttype", 0);
			my $xml_namestring = XMLElement->new($logger, $name_string, "name_string", 0);
			my $xml_descriptor_container = XMLContainer->new($logger, $xml_namestring);
			my $xml_descriptor = XMLElement->new($logger, $xml_descriptor_container, "string_descriptor", 1);
			my $xml_typed_descriptor_container = XMLContainer->new($logger, $xml_enttype, $xml_descriptor);
			my $xml_typed_descriptor = XMLElement->new($logger, $xml_typed_descriptor_container, "typed_descriptor", 1);
			my $xml_entrypoint_container = XMLContainer->new($logger, $xml_node, $xml_typed_descriptor);
			my $xml_entrypoint = XMLElement->new($logger, $xml_entrypoint_container, "entrypoint", 1);
			$xml_entrypoints_container->add($xml_entrypoint);
			next;
		}
		my $node_id = &mask($entrypoint->get("NODEID"));
		my $xml_node = XMLElement->new($logger, $node_id, "node", 0);
		my $xml_entrypoint_container = XMLContainer->new($logger, $xml_node);
		my $ep_mention_id = $entrypoint->get("MENTIONID");
		my $ep_keyframe_id = $entrypoint->get("KEYFRAMEID");
		my $ep_node = $entrypoint->get("NODE");
		foreach my $mention($ep_node->get("MENTIONS")->toarray()){
			next unless $mention->get("MENTIONID") eq $ep_mention_id;
			my $enttype = $mention->get("NIST_TYPE");
			my $xml_enttype = XMLElement->new($logger, $enttype, "enttype", 0);
			my $modality = $mention->get("MODALITY");
			my $fn_manager = FieldNameManager->new($self->get("LOGGER"), $modality);
			foreach my $span($mention->get("SPANS")->toarray()) {
				my $doceid = $span->get("DOCUMENTEID");
				my $start = $span->get("START");
				my $end = $span->get("END");
				my $xml_keyframeid;
				if($modality eq "video") {
					my $keyframe_boundingbox = $self->get("KEYFRAMES_BOUNDINGBOXES")->get("BY_KEY", $ep_keyframe_id);
					$start = $keyframe_boundingbox->get("START");
					$end = $keyframe_boundingbox->get("END");
					$xml_keyframeid = XMLElement->new($logger, $ep_keyframe_id, "keyframeid", 0);
				}
				if($modality eq "image") {
					my $image_boundingbox = $self->get("IMAGES_BOUNDINGBOXES")->get("BY_KEY", $doceid);
					$start = $image_boundingbox->get("START");
					$end = $image_boundingbox->get("END");
				}
				my $xml_doceid = XMLElement->new($logger, $doceid, "doceid", 0);
				my $xml_start = XMLElement->new($logger, $start, $fn_manager->get("FIELDNAME", "start"), 0);
				my $xml_end = XMLElement->new($logger, $end, $fn_manager->get("FIELDNAME", "end"), 0);
				my $xml_descriptor_container = XMLContainer->new($logger, $xml_doceid, $xml_start, $xml_end);
				$xml_descriptor_container = XMLContainer->new($logger, $xml_doceid, $xml_keyframeid, $xml_start, $xml_end)
					if $modality eq "video";
				my $xml_descriptor = XMLElement->new($logger, $xml_descriptor_container, $fn_manager->get("FIELDNAME", "descriptor"), 1);
				my $xml_typed_descriptor_container = XMLContainer->new($logger, $xml_enttype, $xml_descriptor);
				my $xml_typed_descriptor = XMLElement->new($logger, $xml_typed_descriptor_container, "typed_descriptor", 1);
				$xml_entrypoint_container->add($xml_typed_descriptor);
			}
		}
		my $xml_entrypoint = XMLElement->new($logger, $xml_entrypoint_container, "entrypoint", 1);
		$xml_entrypoints_container->add($xml_entrypoint);
	}
	my $xml_entrypoints = XMLElement->new($logger, $xml_entrypoints_container, "entrypoints", 1);
	my $sparql = "";
	$sparql = $self->get("SPARQL") if($self->get("GENERATE_SPARQL"));
	my $xml_sparql = XMLElement->new($logger, $sparql, "sparql", 1);
	my $xml_query_container = XMLContainer->new($logger, $xml_graph, $xml_entrypoints, $xml_sparql);
	my $xml_query = XMLElement->new($logger, $xml_query_container, "graph_query", 1, $query_attributes);
	print $program_output $xml_query->tostring(2);
}

sub get_SPARQL {
	my ($self) = @_;
	my $sparql = SPARQL->new($self->get("LOGGER"), 
								$self->get("QUERY_ID"),
								$self->get("KEYFRAMES_BOUNDINGBOXES"), 
								$self->get("IMAGES_BOUNDINGBOXES"), 
								$self->get("EDGES"), 
								$self->get("ENTRYPOINTS"));
	$sparql->tostring();
}

sub mask {
	my ($input) = @_;

	"?$input";
}

#####################################################################################
# SPARQL
#####################################################################################

package SPARQL;

use parent -norequire, 'Super';

sub new {
	my ($class, $logger, $query_id, $keyframes_boundingboxes, $images_boundingboxes, $edges, $entrypoints) = @_;
	my $self = {
    CLASS => 'SPARQL',
    LOGGER => $logger,
    QUERY_ID => $query_id,
    KEYFRAMES_BOUNDINGBOXES => $keyframes_boundingboxes,
    IMAGES_BOUNDINGBOXES => $images_boundingboxes,
    _NEXT_GROUP_POSTFIX => 10001,
    EDGES => $edges,
    ENTRYPOINTS => $entrypoints,
    SELECT_VARIABLES => "",
    WHERE_CLAUSE_STRING => "",
    WHERE_TEMPLATE => undef,
    TEXT_ENTRYPOINT_CONSTRAINTS => undef,
    IMAGE_ENTRYPOINT_CONSTRAINTS => undef,
    VIDEO_ENTRYPOINT_CONSTRAINTS => undef,
    AUDIO_ENTRYPOINT_CONSTRAINTS => undef,
    SELECT_NODE_VARIABLES_TEMPLATE => undef,
    ALL_NODE_VARIABLES_TEMPLATE => undef,
  };
  bless($self, $class);
  $self->setup_constants();
  $self->process_all_edges();
  $self;
}

sub get_NEXT_GROUP_POSTFIX {
	my ($self) = @_;
	my $group_postfix = $self->get("_NEXT_GROUP_POSTFIX");
	$self->set("_NEXT_GROUP_POSTFIX", $group_postfix+1);
	$group_postfix;
}

sub setup_constants {
	my ($self) = @_;

	$self->{PREFIX} = <<'PREFIX';
PREFIX ldcOnt: <https://tac.nist.gov/tracks/SM-KBP/2018/ontologies/SeedlingOntology#>
	PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
	PREFIX aida:  <https://tac.nist.gov/tracks/SM-KBP/2018/ontologies/InterchangeOntology#>
	PREFIX xsd:   <http://www.w3.org/2001/XMLSchema#>

	Query: QUERYID

PREFIX

	$self->{STRING_ENTRYPOINT_CONSTRAINTS} = <<'STRING_ENTRYPOINT_CONSTRAINTS';
[NID_EP] aida:hasName               "[NAME_STRING]" .
STRING_ENTRYPOINT_CONSTRAINTS

	$self->{TEXT_ENTRYPOINT_CONSTRAINTS} = <<'TEXT_ENTRYPOINT_CONSTRAINTS';
[JUSTIFICATION_EP] a                         aida:TextJustification .
		[JUSTIFICATION_EP] aida:source               "[EPDOCEID]" .
		[JUSTIFICATION_EP] aida:startOffset          [EPSO] .
		[JUSTIFICATION_EP] aida:endOffsetInclusive   [EPEO] .
		FILTER ( ([EPEO] >= [START_OFFSET] && [EPEO] <= [END_OFFSET]) || ([EPSO] >= [START_OFFSET] && [EPSO] <= [END_OFFSET]) ) .
TEXT_ENTRYPOINT_CONSTRAINTS

	$self->{IMAGE_ENTRYPOINT_CONSTRAINTS} = <<'IMAGE_ENTRYPOINT_CONSTRAINTS';
[JUSTIFICATION_EP] a                         aida:ImageJustification .
		[JUSTIFICATION_EP] aida:source               "[EPDOCEID]" .
		[JUSTIFICATION_EP] aida:boundingBox          [BB_EP] .
		[BB_EP] aida:boundingBoxUpperLeftX  [EPULX] .
		[BB_EP] aida:boundingBoxUpperLeftY  [EPULY] .
		[BB_EP] aida:boundingBoxLowerRightX [EPLRX] .
		[BB_EP] aida:boundingBoxLowerRightY [EPLRY] .
		FILTER (([EPULX] >= [UPPER_LEFT_X] && [EPULX] <= [LOWER_RIGHT_X] && [EPULY] <= [LOWER_RIGHT_Y] && [EPULY] >= [UPPER_LEFT_Y]) ||
			([EPLRX] >= [UPPER_LEFT_X] && [EPLRX] <= [LOWER_RIGHT_X] && [EPLRY] <= [LOWER_RIGHT_Y] && [EPLRY] >= [UPPER_LEFT_Y]) ||
			([EPLRX] >= [UPPER_LEFT_X] && [EPLRX] <= [LOWER_RIGHT_X] && [EPULY] <= [LOWER_RIGHT_Y] && [EPULY] >= [UPPER_LEFT_Y]) ||
			([EPULX] >= [UPPER_LEFT_X] && [EPULX] <= [LOWER_RIGHT_X] && [EPLRY] <= [LOWER_RIGHT_Y] && [EPLRY] >= [UPPER_LEFT_Y])) .
IMAGE_ENTRYPOINT_CONSTRAINTS

	$self->{VIDEO_ENTRYPOINT_CONSTRAINTS} = <<'VIDEO_ENTRYPOINT_CONSTRAINTS';
[JUSTIFICATION_EP] a                         aida:KeyFrameVideoJustification .
		[JUSTIFICATION_EP] aida:source               "[EPDOCEID]" .
		[JUSTIFICATION_EP] aida:keyFrame             "[KEYFRAMEID]" .
		[JUSTIFICATION_EP] aida:boundingBox          [BB_EP] .
		[BB_EP] aida:boundingBoxUpperLeftX  [EPULX] .
		[BB_EP] aida:boundingBoxUpperLeftY  [EPULY] .
		[BB_EP] aida:boundingBoxLowerRightX [EPLRX] .
		[BB_EP] aida:boundingBoxLowerRightY [EPLRY] .
		FILTER (([EPULX] >= [UPPER_LEFT_X] && [EPULX] <= [LOWER_RIGHT_X] && [EPULY] <= [LOWER_RIGHT_Y] && [EPULY] >= [UPPER_LEFT_Y]) ||
			([EPLRX] >= [UPPER_LEFT_X] && [EPLRX] <= [LOWER_RIGHT_X] && [EPLRY] <= [LOWER_RIGHT_Y] && [EPLRY] >= [UPPER_LEFT_Y]) ||
			([EPLRX] >= [UPPER_LEFT_X] && [EPLRX] <= [LOWER_RIGHT_X] && [EPULY] <= [LOWER_RIGHT_Y] && [EPULY] >= [UPPER_LEFT_Y]) ||
			([EPULX] >= [UPPER_LEFT_X] && [EPULX] <= [LOWER_RIGHT_X] && [EPLRY] <= [LOWER_RIGHT_Y] && [EPLRY] >= [UPPER_LEFT_Y])) .
VIDEO_ENTRYPOINT_CONSTRAINTS

	$self->{AUDIO_ENTRYPOINT_CONSTRAINTS} = <<'AUDIO_ENTRYPOINT_CONSTRAINTS';
[JUSTIFICATION_EP] a                       aida:AudioJustification .
		[JUSTIFICATION_EP] aida:source             "[EPDOCEID]" .
		[JUSTIFICATION_EP] aida:startTimestamp     [EPST] .
		[JUSTIFICATION_EP] aida:endTimestamp       [EPET] .
		FILTER ( ([EPET] >= [START_TIME] && $epet <= [END_TIME]) || ([EPST] >= [START_TIME] && [EPST] <= [END_TIME]) ) .
AUDIO_ENTRYPOINT_CONSTRAINTS

	$self->{STATEMENT1_TYPE_TRIPLE_TEMPLATE} = "[STATEMENT1]    rdf:object           ldcOnt:[ENTTYPE] .";
	
	$self->{STATEMENT4_TYPE_TRIPLE_TEMPLATE} = "[STATEMENT4]       rdf:object                ldcOnt:[ENTTYPE] .";

	#SELECT ?nid_ep ?nid_ot ?doceid ?sid ?kfid ?so ?eo ?ulx ?uly ?brx ?bry ?st ?et ?cm1cv ?cm2cv ?typecv

	$self->{WHERE_EDGE_TEMPLATE} = <<'END_SPARQL_EDGE_WHERE';
		[STATEMENT1]      a                    rdf:Statement .
		[STATEMENT1]      rdf:object           [OBJECT_NODEID] .
		[STATEMENT1]      rdf:predicate        ldcOnt:[EDGE_TYPE] .
		[STATEMENT1]      rdf:subject          [SUBJECT_NODEID] .
		[STATEMENT1]      aida:confidence      [EDGE_CONFIDENCE] .
		[STATEMENT1]      aida:justifiedBy     [COMPOUND_JUSTIFICATION] .
		[EDGE_CONFIDENCE] aida:confidenceValue [EDGE_CV] .

		[COMPOUND_JUSTIFICATION] a                           aida:CompoundJustification .
		[COMPOUND_JUSTIFICATION] aida:containedJustification [JUSTIFICATION_1] .
		[COMPOUND_JUSTIFICATION] aida:source                 [DOCEID_1] .

		OPTIONAL { [COMPOUND_JUSTIFICATION] aida:containedJustification [JUSTIFICATION_2] . 
			   [COMPOUND_JUSTIFICATION] aida:source                 [DOCEID_2] . }

		OPTIONAL { [JUSTIFICATION_1] a                           aida:TextJustification .
			   [JUSTIFICATION_1] aida:startOffset            [SO_1] .
			   [JUSTIFICATION_1] aida:endOffsetInclusive     [EO_1] }

		OPTIONAL { [JUSTIFICATION_1] a                           aida:ImageJustification .
			   [JUSTIFICATION_1] aida:boundingBox            [BB_1]  .
			   [BB_1]            aida:boundingBoxUpperLeftX  [ULX_1] .
			   [BB_1]            aida:boundingBoxUpperLeftY  [ULY_1] .
			   [BB_1]            aida:boundingBoxLowerRightX [BRX_1] .
			   [BB_1]            aida:boundingBoxLowerRightY [BRY_1] }

		OPTIONAL { [JUSTIFICATION_1] a                           aida:KeyFrameVideoJustification .
			   [JUSTIFICATION_1] aida:keyFrame               [KFID_1] .
			   [JUSTIFICATION_1] aida:boundingBox            [BB_1]  .
			   [BB_1]            aida:boundingBoxUpperLeftX  [ULX_1] .
			   [BB_1]            aida:boundingBoxUpperLeftY  [ULY_1] .
			   [BB_1]            aida:boundingBoxLowerRightX [BRX_1] .
			   [BB_1]            aida:boundingBoxLowerRightY [BRY_1] }

		OPTIONAL { [JUSTIFICATION_1] a                           aida:ShotVideoJustification .
			   [JUSTIFICATION_1] aida:shot                   [SID_1] }

		OPTIONAL { [JUSTIFICATION_1] a                           aida:AudioJustification .
			   [JUSTIFICATION_1] aida:startTimestamp         [ST_1] .
			   [JUSTIFICATION_1] aida:endTimestamp           [ET_1] }

		OPTIONAL { [JUSTIFICATION_2] a                           aida:TextJustification .
			   [JUSTIFICATION_2] aida:startOffset            [SO_2] .
			   [JUSTIFICATION_2] aida:endOffsetInclusive     [EO_2] }

		OPTIONAL { [JUSTIFICATION_2] a                           aida:ImageJustification .
			   [JUSTIFICATION_2] aida:boundingBox            [BB_2]  .
			   [BB_2]            aida:boundingBoxUpperLeftX  [ULX_2] .
			   [BB_2]            aida:boundingBoxUpperLeftY  [ULY_2] .
			   [BB_2]            aida:boundingBoxLowerRightX [BRX_2] .
			   [BB_2]            aida:boundingBoxLowerRightY [BRY_2] }

		OPTIONAL { [JUSTIFICATION_2] a                           aida:KeyFrameVideoJustification .
			   [JUSTIFICATION_2] aida:keyFrame               [KFID_2] .
			   [JUSTIFICATION_2] aida:boundingBox            [BB_2]  .
			   [BB_2]            aida:boundingBoxUpperLeftX  [ULX_2] .
			   [BB_2]            aida:boundingBoxUpperLeftY  [ULY_2] .
			   [BB_2]            aida:boundingBoxLowerRightX [BRX_2] .
			   [BB_2]            aida:boundingBoxLowerRightY [BRY_2] }

		OPTIONAL { [JUSTIFICATION_2] a                           aida:ShotVideoJustification .
			   [JUSTIFICATION_2] aida:shot                   [SID_2] }

		OPTIONAL { [JUSTIFICATION_2] a                           aida:AudioJustification .
			   [JUSTIFICATION_2] aida:startTimestamp         [ST_2] .
			   [JUSTIFICATION_2] aida:endTimestamp           [ET_2] }

END_SPARQL_EDGE_WHERE

	$self->{WHERE_NODE_TEMPLATE} = <<'END_SPARQL_NODE_WHERE';
		[STATEMENT1]    a                    rdf:Statement .
		[STATEMENT1_TYPE_TRIPLE_TEMPLATE]
		[STATEMENT1]    rdf:predicate        rdf:type .
		[STATEMENT1]    rdf:subject          [NID_OT] .
		[STATEMENT1]    aida:justifiedBy     [JUSTIFICATION] .
		[JUSTIFICATION] aida:source          [DOCEID] .
		[JUSTIFICATION] aida:confidence      [CONFIDENCE] .
		[CONFIDENCE]    aida:confidenceValue [TYPE_CV] .

		[CLUSTER]        a                    aida:SameAsCluster .
		[STATEMENT2]     a                    aida:ClusterMembership .
		[STATEMENT2]     aida:cluster         [CLUSTER] .
		[STATEMENT2]     aida:clusterMember   [NID_EP] .
		[STATEMENT2]     aida:confidence      [CM1_CONFIDENCE] .
		[CM1_CONFIDENCE] aida:confidenceValue [CM1_CV] .

		[STATEMENT3]     a                    aida:ClusterMembership .
		[STATEMENT3]     aida:cluster         [CLUSTER] .
		[STATEMENT3]     aida:clusterMember   [NID_OT] .
		[STATEMENT3]     aida:confidence      [CM2_CONFIDENCE] .
		[CM2_CONFIDENCE] aida:confidenceValue [CM2_CV] .

		[STATEMENT4]       a                         rdf:Statement .
		[STATEMENT4_TYPE_TRIPLE_TEMPLATE]
		[STATEMENT4]       rdf:predicate             rdf:type .
		[STATEMENT4]       rdf:subject               [NID_EP] .
		[STATEMENT4]       aida:justifiedBy          [JUSTIFICATION_EP] .
		[ENTRYPOINT_CONSTRAINTS]

		OPTIONAL { [JUSTIFICATION] a                  aida:TextJustification .
			   [JUSTIFICATION] aida:startOffset            [SO] .
			   [JUSTIFICATION] aida:endOffsetInclusive     [EO] }

		OPTIONAL { [JUSTIFICATION] a                  aida:ImageJustification .
			   [JUSTIFICATION] aida:boundingBox            [BB]  .
			   [BB]            aida:boundingBoxUpperLeftX  [ULX] .
			   [BB]            aida:boundingBoxUpperLeftY  [ULY] .
			   [BB]            aida:boundingBoxLowerRightX [BRX] .
			   [BB]            aida:boundingBoxLowerRightY [BRY] }

		OPTIONAL { [JUSTIFICATION] a                  aida:KeyFrameVideoJustification .
			   [JUSTIFICATION] aida:keyFrame               [KFID] .
			   [JUSTIFICATION] aida:boundingBox            [BB]  .
			   [BB]            aida:boundingBoxUpperLeftX  [ULX] .
			   [BB]            aida:boundingBoxUpperLeftY  [ULY] .
			   [BB]            aida:boundingBoxLowerRightX [BRX] .
			   [BB]            aida:boundingBoxLowerRightY [BRY] }

		OPTIONAL { [JUSTIFICATION] a                  aida:ShotVideoJustification .
			   [JUSTIFICATION] aida:shot                   [SID] }

		OPTIONAL { [JUSTIFICATION] a                  aida:AudioJustification .
			   [JUSTIFICATION] aida:startTimestamp         [ST] .
			   [JUSTIFICATION] aida:endTimestamp           [ET] }
END_SPARQL_NODE_WHERE

    $self->{"SELECT_NODE_VARIABLES_TEMPLATE"} = [qw(nid_ep nid_ot doceid sid kfid so eo ulx uly brx bry st et cm1_cv cm2_cv type_cv
													doceid_1 sid_1 kfid_1 so_1 eo_1 ulx_1 uly_1 brx_1 bry_1 st_1 et_1
													doceid_2 sid_2 kfid_2 so_2 eo_2 ulx_2 uly_2 brx_2 bry_2 st_2 et_2)];

    $self->{"ALL_NODE_VARIABLES_TEMPLATE"} = [qw(nid_ep nid_ot doceid sid kfid so eo ulx uly brx bry st et cm1_cv cm2_cv type_cv
													statement1 statement2 statement3 statement4 cluster justification justification_ep bb
													confidence type_cv cm1_confidence cm2_confidence bb_ep epulx epuly eplrx eplry epst
													epet epso epeo)];

    $self->{"ALL_EDGE_VARIABLES_TEMPLATE"} = [qw(statement1 edge_confidence compound_justification edge_cv
													justification_1 doceid_1 sid_1 kfid_1 so_1 eo_1 ulx_1 uly_1 brx_1 bry_1 st_1 et_1 bb_1
													justification_2 doceid_2 sid_2 kfid_2 so_2 eo_2 ulx_2 uly_2 brx_2 bry_2 st_2 et_2 bb_2)]
}

sub process_all_edges {
	my ($self) = @_;
	foreach my $edge($self->get("EDGES")->toarray()) {
		$self->process_edge($edge);
	}
}

sub process_edge {
	my ($self, $edge) = @_;
	my $subject = $edge->get("SUBJECT");
	# Get the subject type
	my $subject_type;
	foreach my $nist_type($subject->get("NIST_TYPES")) {
		$subject_type = $nist_type
			if($edge->get("PREDICATE") =~ /$nist_type/)
	}
	my $subject_nodevariable = $self->process_node($subject, $subject_type);
	my $object = $edge->get("OBJECT");
	# See if you can find a single object type
	my $object_type;
	if($object->get("NIST_TYPES") == 1) {
		# If there is a single type for the object
		($object_type) = $object->get("NIST_TYPES");
	}
	else {
		# otherwise, see if you obtain this information from the entrypoints
		foreach my $entrypoint(@{$self->get("ENTRYPOINTS")}) {
			next if $entrypoint->{TYPE} eq "STRING_ENTRYPOINT";
			if($object->get("NODEID") eq $entrypoint->{NODEID}) {
				$object_type = $object->get("MENTION", $entrypoint->{"MENTIONID"})->get("NIST_TYPE") unless($object_type);
				last if $object_type;
			}
		}
	}
	my $object_nodevariable = $self->process_node($object, $object_type);
	my $edge_type = $edge->get("PREDICATE");
	# Process the edge
	my $group_postfix = $self->get("NEXT_GROUP_POSTFIX");
	my $where_clause = $self->get("WHERE_EDGE_TEMPLATE");
	$where_clause =~ s/\[SUBJECT_NODEID\]/$subject_nodevariable/g;
	$where_clause =~ s/\[OBJECT_NODEID\]/$object_nodevariable/g;
	$where_clause =~ s/\[EDGE_TYPE\]/$edge_type/g;
	my @select_node_variables_template = @{$self->get("SELECT_NODE_VARIABLES_TEMPLATE")};
	my %select_node_variables_template = map {$_=>1} @select_node_variables_template;
	foreach my $variable(@{$self->get("ALL_EDGE_VARIABLES_TEMPLATE")}) {
		my $is_select_variable = $select_node_variables_template{$variable};
		my $new_variable = "$variable\_$group_postfix";
		$self->set("SELECT_VARIABLES", $self->get("SELECT_VARIABLES") . " ?" . $new_variable) if $is_select_variable;
		my $old_variable = "\\[" . uc $variable . "\\]";
		$where_clause =~ s/$old_variable/\?$new_variable/gs;
	}
	$self->set("WHERE_CLAUSE_STRING", $self->get("WHERE_CLAUSE_STRING") . "\n" . $where_clause);
}

sub process_node {
	my ($self, $node, $type) = @_;
	my $group_postfix = $self->get("NEXT_GROUP_POSTFIX");
	my $where_clause = $self->get("WHERE_NODE_TEMPLATE");
	my @select_node_variables_template = @{$self->get("SELECT_NODE_VARIABLES_TEMPLATE")};
	my %select_node_variables_template = map {$_=>1} @select_node_variables_template;
	my $statement1_type_triple_template = $self->get("STATEMENT1_TYPE_TRIPLE_TEMPLATE");
	my $statement4_type_triple_template = $self->get("STATEMENT4_TYPE_TRIPLE_TEMPLATE");
	my $string_entrypoint_constraints = $self->get("STRING_ENTRYPOINT_CONSTRAINTS");
	my $text_entrypoint_constraints = $self->get("TEXT_ENTRYPOINT_CONSTRAINTS");
	my $image_entrypoint_constraints = $self->get("IMAGE_ENTRYPOINT_CONSTRAINTS");
	my $video_entrypoint_constraints = $self->get("VIDEO_ENTRYPOINT_CONSTRAINTS");
	my $audio_entrypoint_constraints = $self->get("AUDIO_ENTRYPOINT_CONSTRAINTS");
	my ($retval_nodevariable, $retval_clustervariable);
	foreach my $variable(@{$self->get("ALL_NODE_VARIABLES_TEMPLATE")}) {
		my $is_select_variable = $select_node_variables_template{$variable};
		my $new_variable = "$variable\_$group_postfix";
		$retval_nodevariable = $new_variable if($variable eq "nid_ot");
		$self->set("SELECT_VARIABLES", $self->get("SELECT_VARIABLES") . " ?" . $new_variable) if $is_select_variable;
		my $old_variable = "\\[" . uc $variable . "\\]";
		$where_clause =~ s/$old_variable/\?$new_variable/gs;
		$statement1_type_triple_template =~ s/$old_variable/\?$new_variable/gs;
		$statement4_type_triple_template =~ s/$old_variable/\?$new_variable/gs;
		$string_entrypoint_constraints =~ s/$old_variable/\?$new_variable/gs;
		$text_entrypoint_constraints =~ s/$old_variable/\?$new_variable/gs;
		$image_entrypoint_constraints =~ s/$old_variable/\?$new_variable/gs;
		$video_entrypoint_constraints =~ s/$old_variable/\?$new_variable/gs;
		$audio_entrypoint_constraints =~ s/$old_variable/\?$new_variable/gs;
	}
	if($type) {
		$statement1_type_triple_template =~ s/\[ENTTYPE\]/$type/;
		$statement4_type_triple_template =~ s/\[ENTTYPE\]/$type/;
		$where_clause =~ s/\[STATEMENT1_TYPE_TRIPLE_TEMPLATE\]\n/$statement1_type_triple_template\n/g;
		$where_clause =~ s/\[STATEMENT4_TYPE_TRIPLE_TEMPLATE\]\n/$statement4_type_triple_template\n/g;
	}
	else {
		$where_clause =~ s/\n\s+?\[STATEMENT1_TYPE_TRIPLE_TEMPLATE\]\n/\n/gs;
		$where_clause =~ s/\n\s+?\[STATEMENT4_TYPE_TRIPLE_TEMPLATE\]\n/\n/gs;
	}
	my $the_entrypoint;
	foreach my $entrypoint(@{$self->get("ENTRYPOINTS")}) {
		if($node->get("NODEID") eq $entrypoint->{NODEID}) {
			$the_entrypoint = $entrypoint;
		}
	}
	if($the_entrypoint) {
		# replace the [ENTRYPOINT_CONSTRAINTS] with appropriate string
		if($the_entrypoint->{TYPE} eq "STRING_ENTRYPOINT") {
			my $text_string = $the_entrypoint->{TEXT_STRING};
			$string_entrypoint_constraints =~ s/\[NAME_STRING\]/$text_string/g;
			$where_clause =~ s/\[ENTRYPOINT_CONSTRAINTS\]/$string_entrypoint_constraints/;
		}
		elsif($the_entrypoint->{TYPE} eq "NONSTRING_ENTRYPOINT") {
			my $modality = $node->get("MENTION", $the_entrypoint->{MENTIONID})->get("MODALITY");
			my ($span) = $node->get("MENTION", $the_entrypoint->{MENTIONID})->get("SPANS")->toarray();
			my ($start, $end) = ($span->get("START"), $span->get("END"));
			my $doceid = $span->get("DOCUMENTEID");
			my $keyframeid;
			if($modality eq "text") {
				$text_entrypoint_constraints =~ s/\[START_OFFSET\]/$start/gs;
				$text_entrypoint_constraints =~ s/\[END_OFFSET\]/$end/gs;
				$text_entrypoint_constraints =~ s/\[EPDOCEID\]/$doceid/gs;
				$where_clause =~ s/\[ENTRYPOINT_CONSTRAINTS\]/$text_entrypoint_constraints/;
			}
			elsif($modality eq "image") {
				if($self->get("IMAGES_BOUNDINGBOXES")->exists($doceid)) {
					my $image_boundingbox = $self->get("IMAGES_BOUNDINGBOXES")->get("BY_KEY", $doceid);
					$start = $image_boundingbox->get("START");
					$end = $image_boundingbox->get("END");
					my ($ulx, $uly) = split(",", $start);
					my ($lrx, $lry) = split(",", $end);
					$image_entrypoint_constraints =~ s/\[EPDOCEID\]/$doceid/gs;
					$image_entrypoint_constraints =~ s/\[UPPER_LEFT_X\]/$ulx/gs;
					$image_entrypoint_constraints =~ s/\[UPPER_LEFT_Y\]/$uly/gs;
					$image_entrypoint_constraints =~ s/\[LOWER_RIGHT_X\]/$lrx/gs;
					$image_entrypoint_constraints =~ s/\[LOWER_RIGHT_Y\]/$lry/gs;
					$where_clause =~ s/\[ENTRYPOINT_CONSTRAINTS\]/$image_entrypoint_constraints/;
				}
				else {
					$where_clause =~ s/\[ENTRYPOINT_CONSTRAINTS\]\n//gs;
				}
			}
			elsif($modality eq "video") {
				$keyframeid = $the_entrypoint->get("KEYFRAMEID");
				my $keyframe_boundingbox = $self->get("KEYFRAMES_BOUNDINGBOXES")->get("BY_KEY", $keyframeid);
				$start = $keyframe_boundingbox->get("START");
				$end = $keyframe_boundingbox->get("END");
				my ($ulx, $uly) = split(",", $start);
				my ($lrx, $lry) = split(",", $end);
				$video_entrypoint_constraints =~ s/\[EPDOCEID\]/$doceid/gs;
				$video_entrypoint_constraints =~ s/\[UPPER_LEFT_X\]/$ulx/gs;
				$video_entrypoint_constraints =~ s/\[UPPER_LEFT_Y\]/$uly/gs;
				$video_entrypoint_constraints =~ s/\[LOWER_RIGHT_X\]/$lrx/gs;
				$video_entrypoint_constraints =~ s/\[LOWER_RIGHT_Y\]/$lry/gs;
				$video_entrypoint_constraints =~ s/\[KEYFRAMEID\]/$keyframeid/gs;
				$where_clause =~ s/\[ENTRYPOINT_CONSTRAINTS\]/$video_entrypoint_constraints/;
			}
			elsif($modality eq "audio") {
				$audio_entrypoint_constraints =~ s/\[EPDOCEID\]/$doceid/gs;
				$audio_entrypoint_constraints =~ s/\[START_TIME\]/$start/g;
				$audio_entrypoint_constraints =~ s/\[END_TIME\]/$end/g;
				$where_clause =~ s/\[ENTRYPOINT_CONSTRAINTS\]/$audio_entrypoint_constraints/;
			}
		}
	}
	else {
		$where_clause =~ s/\[ENTRYPOINT_CONSTRAINTS\]\n//gs;
	}
	$self->set("WHERE_CLAUSE_STRING", $self->get("WHERE_CLAUSE_STRING") . "\n" . $where_clause);
	$retval_nodevariable;
}

sub tostring {
	my ($self) = @_;
	my $query_id = $self->get("QUERY_ID");
	my $sparql = "\n\t<![CDATA[\n";
	$sparql .= "\t". $self->get("PREFIX");
	$sparql .= "\n\tSELECT";
	$sparql .= $self->get("SELECT_VARIABLES");
	$sparql .= "\n\tWHERE {";
	$sparql .= $self->get("WHERE_CLAUSE_STRING");
	$sparql .= "\t}\n";
	$sparql .= "\t]]>\n";
	$sparql =~ s/QUERYID/$query_id/;

	$sparql;
}

#####################################################################################
# FieldNameManager
#####################################################################################

package FieldNameManager;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $modality) = @_;
  my $self = {
    CLASS => 'FieldNameManager',
    MODALITY => $modality,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub get_FIELDNAME {
	my ($self, $field) = @_;
	my $retVal = $field;
	my $modality = $self->get("MODALITY");
	if($field eq "start") {
		$retVal = "topleft" if $modality eq "video" or $modality eq "image";
	}
	elsif($field eq "end") {
		$retVal = "bottomright" if $modality eq "video" or $modality eq "image";
	}
	elsif($field eq "descriptor") {
		$retVal = $modality . "_" . $field;
	}
	$retVal;
}

#####################################################################################
# XMLAttributes
#####################################################################################

package XMLAttributes;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'XMLAttribute');
  $self->{CLASS} = 'XMLAttributes';
  $self->{LOGGER} = $logger;
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
  my ($class, $logger, $element, $name, $newline, $attributes) = @_;
  my $self = {
    CLASS => 'XMLElement',
    NAME => $name,
    NEWLINE => $newline,
    ATTRIBUTES => $attributes,
    ELEMENT => $element,
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

sub tostring {
	my ($self, $indent) = @_;
	
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

sub tostring {
	my ($self, $indent) = @_;
	my $retVal = "";
	foreach my $xml_elements($self->toarray()) {
		$retVal .= $xml_elements->tostring($indent);
	}
	$retVal;
}

#####################################################################################
# EncodingFormatToModalityMappings
#####################################################################################

package EncodingFormatToModalityMappings;

use parent -norequire, 'Container', 'Super';

sub new {
	my ($class, $logger, $parameters) = @_;
	my $self = $class->SUPER::new($logger, 'RAW');
	$self->{CLASS} = 'EncodingFormatToModalityMappings';
	$self->{PARAMETERS} = $parameters;
	$self->{LOGGER} = $logger;
	bless($self, $class);
	$self->load_data();
	$self;
}

sub load_data {
	my ($self) = @_;
	my $filehandler = FileHandler->new($self->get("LOGGER"), $self->get("PARAMETERS")->get("ENCODINGFORMAT_TO_MODALITYMAPPING_FILE"));
	my $entries = $filehandler->get("ENTRIES");
	foreach my $entry($entries->toarray()) {
		my $encoding_format = $entry->get("encoding_format");
		my $modality = $entry->get("modality");
		$self->add($modality, $encoding_format);
	}
}

1;
