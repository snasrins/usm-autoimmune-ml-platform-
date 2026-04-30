# Code Citations

## License: unknown
https://github.com/laserprec/simFlaskApi/blob/1502f18de7dd61dee6c54152b6e5c26af43132be/migrations/versions/54bac289a2a4_.py

```
The permission error is because you're trying to create a file in a directory owned by root. Let's create it via SSH instead:

```bash
# SSH to server
cd ~/usm-autoimmune-ml-platform/alembic/versions

# Create the migration file
cat > add_validation_queue_table.py << 'EOF'
"""Add validation_queue table for unstructured pipeline

Revision ID: validation_queue_001
Revises: 9a2e81360415
Create Date: 2026-04-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'validation_queue_001'
down_revision: Union[str, None] = '9a2e81360415'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create validation_queue table for human-in-the-loop workflow"""
    
    # Create validation_queue table
    op.create_table(
        'validation_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=True),
        sa.Column('stage', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending_review'),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('validation_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_validation_status', 'validation_queue', ['status'], unique=False)
    op.create_index('idx_validation_stage', 'validation_queue', ['stage'], unique=False)
    op.create_index('idx_validation_assigned',
```


## License: unknown
https://github.com/laserprec/simFlaskApi/blob/1502f18de7dd61dee6c54152b6e5c26af43132be/migrations/versions/54bac289a2a4_.py

```
The permission error is because you're trying to create a file in a directory owned by root. Let's create it via SSH instead:

```bash
# SSH to server
cd ~/usm-autoimmune-ml-platform/alembic/versions

# Create the migration file
cat > add_validation_queue_table.py << 'EOF'
"""Add validation_queue table for unstructured pipeline

Revision ID: validation_queue_001
Revises: 9a2e81360415
Create Date: 2026-04-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'validation_queue_001'
down_revision: Union[str, None] = '9a2e81360415'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create validation_queue table for human-in-the-loop workflow"""
    
    # Create validation_queue table
    op.create_table(
        'validation_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=True),
        sa.Column('stage', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending_review'),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('validation_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_validation_status', 'validation_queue', ['status'], unique=False)
    op.create_index('idx_validation_stage', 'validation_queue', ['stage'], unique=False)
    op.create_index('idx_validation_assigned',
```


## License: unknown
https://github.com/laserprec/simFlaskApi/blob/1502f18de7dd61dee6c54152b6e5c26af43132be/migrations/versions/54bac289a2a4_.py

```
The permission error is because you're trying to create a file in a directory owned by root. Let's create it via SSH instead:

```bash
# SSH to server
cd ~/usm-autoimmune-ml-platform/alembic/versions

# Create the migration file
cat > add_validation_queue_table.py << 'EOF'
"""Add validation_queue table for unstructured pipeline

Revision ID: validation_queue_001
Revises: 9a2e81360415
Create Date: 2026-04-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'validation_queue_001'
down_revision: Union[str, None] = '9a2e81360415'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create validation_queue table for human-in-the-loop workflow"""
    
    # Create validation_queue table
    op.create_table(
        'validation_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=True),
        sa.Column('stage', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending_review'),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('validation_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_validation_status', 'validation_queue', ['status'], unique=False)
    op.create_index('idx_validation_stage', 'validation_queue', ['stage'], unique=False)
    op.create_index('idx_validation_assigned',
```


## License: unknown
https://github.com/laserprec/simFlaskApi/blob/1502f18de7dd61dee6c54152b6e5c26af43132be/migrations/versions/54bac289a2a4_.py

```
The permission error is because you're trying to create a file in a directory owned by root. Let's create it via SSH instead:

```bash
# SSH to server
cd ~/usm-autoimmune-ml-platform/alembic/versions

# Create the migration file
cat > add_validation_queue_table.py << 'EOF'
"""Add validation_queue table for unstructured pipeline

Revision ID: validation_queue_001
Revises: 9a2e81360415
Create Date: 2026-04-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'validation_queue_001'
down_revision: Union[str, None] = '9a2e81360415'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create validation_queue table for human-in-the-loop workflow"""
    
    # Create validation_queue table
    op.create_table(
        'validation_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=True),
        sa.Column('stage', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending_review'),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('validation_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_validation_status', 'validation_queue', ['status'], unique=False)
    op.create_index('idx_validation_stage', 'validation_queue', ['stage'], unique=False)
    op.create_index('idx_validation_assigned',
```


## License: unknown
https://github.com/laserprec/simFlaskApi/blob/1502f18de7dd61dee6c54152b6e5c26af43132be/migrations/versions/54bac289a2a4_.py

```
The permission error is because you're trying to create a file in a directory owned by root. Let's create it via SSH instead:

```bash
# SSH to server
cd ~/usm-autoimmune-ml-platform/alembic/versions

# Create the migration file
cat > add_validation_queue_table.py << 'EOF'
"""Add validation_queue table for unstructured pipeline

Revision ID: validation_queue_001
Revises: 9a2e81360415
Create Date: 2026-04-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'validation_queue_001'
down_revision: Union[str, None] = '9a2e81360415'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create validation_queue table for human-in-the-loop workflow"""
    
    # Create validation_queue table
    op.create_table(
        'validation_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=True),
        sa.Column('stage', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending_review'),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('validation_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_validation_status', 'validation_queue', ['status'], unique=False)
    op.create_index('idx_validation_stage', 'validation_queue', ['stage'], unique=False)
    op.create_index('idx_validation_assigned',
```


## License: unknown
https://github.com/laserprec/simFlaskApi/blob/1502f18de7dd61dee6c54152b6e5c26af43132be/migrations/versions/54bac289a2a4_.py

```
The permission error is because you're trying to create a file in a directory owned by root. Let's create it via SSH instead:

```bash
# SSH to server
cd ~/usm-autoimmune-ml-platform/alembic/versions

# Create the migration file
cat > add_validation_queue_table.py << 'EOF'
"""Add validation_queue table for unstructured pipeline

Revision ID: validation_queue_001
Revises: 9a2e81360415
Create Date: 2026-04-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'validation_queue_001'
down_revision: Union[str, None] = '9a2e81360415'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create validation_queue table for human-in-the-loop workflow"""
    
    # Create validation_queue table
    op.create_table(
        'validation_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=True),
        sa.Column('stage', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending_review'),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('validation_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_validation_status', 'validation_queue', ['status'], unique=False)
    op.create_index('idx_validation_stage', 'validation_queue', ['stage'], unique=False)
    op.create_index('idx_validation_assigned',
```

