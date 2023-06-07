drop table process_metadata;

CREATE TABLE [dbo].[process_metadata](
	[tibco_engine] [varchar](50) NULL,
	[project_name] [varchar](1500) NULL,
	[process_name] [varchar](100) NULL,
	[activity_name] [varchar](50) NULL,
	[activity_type] [varchar](200) NULL,
	[act_sharedresource] [varchar](100) NULL,
	[act_statement] [text] NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

delete process_metadata;

select * from process_metadata